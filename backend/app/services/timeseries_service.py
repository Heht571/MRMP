from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, asc, func, text
from sqlalchemy.orm import selectinload

from app.models.timeseries import TimeseriesData


class TimeseriesService:
    """时序数据服务 - 基于 ref_id 关联"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._timescale_enabled: Optional[bool] = None

    async def _check_timescale(self) -> bool:
        """检查 TimescaleDB 是否可用"""
        if self._timescale_enabled is not None:
            return self._timescale_enabled

        try:
            result = await self.db.execute(
                text("SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'timeseries_data'")
            )
            self._timescale_enabled = result.fetchone() is not None
        except Exception:
            self._timescale_enabled = False

        return self._timescale_enabled

    @staticmethod
    def generate_ref_id(instance_id: UUID, attribute_name: str) -> str:
        """生成时序数据引用ID"""
        return f"ts:{attribute_name}:{str(instance_id)}"

    @staticmethod
    def parse_ref_id(ref_id: str) -> Dict[str, str]:
        """解析 ref_id，返回 {attribute_name, instance_id}"""
        parts = ref_id.split(':', 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid ref_id format: {ref_id}")
        return {
            'attribute_name': parts[1],
            'instance_id': parts[2]
        }

    async def write_datapoint(
        self,
        instance_id: UUID,
        attribute_name: str,
        values: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> TimeseriesData:
        """写入单个时序数据点"""
        if timestamp is None:
            timestamp = datetime.utcnow()

        ref_id = self.generate_ref_id(instance_id, attribute_name)

        datapoint = TimeseriesData(
            ref_id=ref_id,
            instance_id=instance_id,
            attribute_name=attribute_name,
            timestamp=timestamp,
            value=values
        )
        self.db.add(datapoint)
        await self.db.flush()
        return datapoint

    async def write_datapoints(
        self,
        instance_id: UUID,
        attribute_name: str,
        data_points: List[Dict[str, Any]]
    ) -> List[TimeseriesData]:
        """批量写入时序数据点"""
        datapoints = []
        now = datetime.utcnow()
        ref_id = self.generate_ref_id(instance_id, attribute_name)

        for point in data_points:
            ts = point.get('timestamp')
            if ts and isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))

            datapoint = TimeseriesData(
                ref_id=ref_id,
                instance_id=instance_id,
                attribute_name=attribute_name,
                timestamp=ts or now,
                value=point.get('values', {})
            )
            datapoints.append(datapoint)

        self.db.add_all(datapoints)
        await self.db.flush()
        return datapoints

    async def write_by_ref(
        self,
        ref_id: str,
        values: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> TimeseriesData:
        """通过 ref_id 写入单个数据点"""
        if timestamp is None:
            timestamp = datetime.utcnow()

        parsed = self.parse_ref_id(ref_id)
        instance_id = UUID(parsed['instance_id'])
        attribute_name = parsed['attribute_name']

        return await self.write_datapoint(
            instance_id=instance_id,
            attribute_name=attribute_name,
            values=values,
            timestamp=timestamp
        )

    async def write_batch_by_ref(
        self,
        ref_id: str,
        data_points: List[Dict[str, Any]]
    ) -> List[TimeseriesData]:
        """通过 ref_id 批量写入数据点"""
        parsed = self.parse_ref_id(ref_id)
        instance_id = UUID(parsed['instance_id'])
        attribute_name = parsed['attribute_name']

        return await self.write_datapoints(
            instance_id=instance_id,
            attribute_name=attribute_name,
            data_points=data_points
        )

    async def query_by_ref(
        self,
        ref_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[TimeseriesData]:
        """通过 ref_id 查询时序数据"""
        result = await self.db.execute(
            select(TimeseriesData)
            .where(
                and_(
                    TimeseriesData.ref_id == ref_id,
                    TimeseriesData.timestamp >= start_time,
                    TimeseriesData.timestamp <= end_time
                )
            )
            .order_by(TimeseriesData.timestamp.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def query_range(
        self,
        instance_id: UUID,
        attribute_name: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[TimeseriesData]:
        """查询时间范围内的原始时序数据"""
        ref_id = self.generate_ref_id(instance_id, attribute_name)
        return await self.query_by_ref(ref_id, start_time, end_time, limit)

    async def query_aggregated(
        self,
        instance_id: UUID,
        attribute_name: str,
        start_time: datetime,
        end_time: datetime,
        bucket: str = '1 hour',
        metrics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """按时间桶聚合查询时序数据"""
        if not metrics:
            metrics = ['cpu', 'memory', 'disk', 'network']

        is_timescale = await self._check_timescale()

        if is_timescale:
            return await self._query_aggregated_timescale(
                instance_id, attribute_name, start_time, end_time, bucket, metrics
            )
        else:
            return await self._query_aggregated_pg(
                instance_id, attribute_name, start_time, end_time, bucket, metrics
            )

    async def _query_aggregated_timescale(
        self,
        instance_id: UUID,
        attribute_name: str,
        start_time: datetime,
        end_time: datetime,
        bucket: str,
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """TimescaleDB 聚合查询"""
        ref_id = self.generate_ref_id(instance_id, attribute_name)

        select_parts = [f"time_bucket('{bucket}', timestamp) AS bucket"]
        for metric in metrics:
            select_parts.append(f"avg((value->>'{metric}')::float) as {metric}_avg")
            select_parts.append(f"max((value->>'{metric}')::float) as {metric}_max")
            select_parts.append(f"min((value->>'{metric}')::float) as {metric}_min")

        query = text(f"""
            SELECT {', '.join(select_parts)}
            FROM timeseries_data
            WHERE ref_id = :ref_id
              AND timestamp >= :start_time
              AND timestamp <= :end_time
            GROUP BY bucket
            ORDER BY bucket ASC
        """)

        result = await self.db.execute(
            query,
            {
                'ref_id': ref_id,
                'start_time': start_time,
                'end_time': end_time
            }
        )

        return [dict(row._mapping) for row in result.fetchall()]

    async def _query_aggregated_pg(
        self,
        instance_id: UUID,
        attribute_name: str,
        start_time: datetime,
        end_time: datetime,
        bucket: str,
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """原生 PostgreSQL 聚合查询"""
        ref_id = self.generate_ref_id(instance_id, attribute_name)
        bucket_interval = self._convert_bucket_to_interval(bucket)

        select_parts = [
            f"date_bin('{bucket_interval}', timestamp, '{start_time}') AS bucket"
        ]
        for metric in metrics:
            select_parts.append(f"avg((value->>'{metric}')::float) as {metric}_avg")
            select_parts.append(f"max((value->>'{metric}')::float) as {metric}_max")
            select_parts.append(f"min((value->>'{metric}')::float) as {metric}_min")

        query = text(f"""
            SELECT {', '.join(select_parts)}
            FROM timeseries_data
            WHERE ref_id = :ref_id
              AND timestamp >= :start_time
              AND timestamp <= :end_time
            GROUP BY bucket
            ORDER BY bucket ASC
        """)

        result = await self.db.execute(
            query,
            {
                'ref_id': ref_id,
                'start_time': start_time,
                'end_time': end_time
            }
        )

        return [dict(row._mapping) for row in result.fetchall()]

    def _convert_bucket_to_interval(self, bucket: str) -> str:
        """将 time_bucket 格式转换为 date_bin 格式"""
        mapping = {
            '1 minute': '1 minute',
            '5 minute': '5 minutes',
            '15 minute': '15 minutes',
            '30 minute': '30 minutes',
            '1 hour': '1 hour',
            '6 hour': '6 hours',
            '1 day': '1 day',
            '1 week': '1 week'
        }
        return mapping.get(bucket, '1 hour')

    async def get_latest(
        self,
        instance_id: UUID,
        attribute_name: str,
        limit: int = 10
    ) -> List[TimeseriesData]:
        """获取最新的 N 条时序数据"""
        ref_id = self.generate_ref_id(instance_id, attribute_name)

        result = await self.db.execute(
            select(TimeseriesData)
            .where(TimeseriesData.ref_id == ref_id)
            .order_by(TimeseriesData.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_by_ref(
        self,
        ref_id: str,
        limit: int = 10
    ) -> List[TimeseriesData]:
        """通过 ref_id 获取最新数据"""
        result = await self.db.execute(
            select(TimeseriesData)
            .where(TimeseriesData.ref_id == ref_id)
            .order_by(TimeseriesData.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_value(
        self,
        instance_id: UUID,
        attribute_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取最新的时序数据点"""
        latest = await self.get_latest(instance_id, attribute_name, limit=1)
        if latest:
            dp = latest[0]
            return {
                'timestamp': dp.timestamp.isoformat(),
                'values': dp.value
            }
        return None

    async def get_statistics(
        self,
        instance_id: UUID,
        attribute_name: str,
        start_time: datetime,
        end_time: datetime,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """获取时序数据的统计信息"""
        if not metrics:
            metrics = ['cpu', 'memory', 'disk', 'network']

        ref_id = self.generate_ref_id(instance_id, attribute_name)

        stats = {
            'count': 0,
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'metrics': {}
        }

        # 使用原生 SQL 查询统计信息
        for metric in metrics:
            metric_stats = {}

            # 查询平均值
            avg_query = text(f"""
                SELECT avg((value->>'{metric}')::float) as avg_val
                FROM timeseries_data
                WHERE ref_id = :ref_id
                  AND timestamp >= :start_time
                  AND timestamp <= :end_time
            """)
            avg_result = await self.db.execute(avg_query, {
                'ref_id': ref_id,
                'start_time': start_time,
                'end_time': end_time
            })
            row = avg_result.fetchone()
            metric_stats['avg'] = row[0] if row else None

            # 查询最大值
            max_query = text(f"""
                SELECT max((value->>'{metric}')::float) as max_val
                FROM timeseries_data
                WHERE ref_id = :ref_id
                  AND timestamp >= :start_time
                  AND timestamp <= :end_time
            """)
            max_result = await self.db.execute(max_query, {
                'ref_id': ref_id,
                'start_time': start_time,
                'end_time': end_time
            })
            row = max_result.fetchone()
            metric_stats['max'] = row[0] if row else None

            # 查询最小值
            min_query = text(f"""
                SELECT min((value->>'{metric}')::float) as min_val
                FROM timeseries_data
                WHERE ref_id = :ref_id
                  AND timestamp >= :start_time
                  AND timestamp <= :end_time
            """)
            min_result = await self.db.execute(min_query, {
                'ref_id': ref_id,
                'start_time': start_time,
                'end_time': end_time
            })
            row = min_result.fetchone()
            metric_stats['min'] = row[0] if row else None

            stats['metrics'][metric] = metric_stats

        # 查询总数
        count_query = text("""
            SELECT count(*) FROM timeseries_data
            WHERE ref_id = :ref_id
              AND timestamp >= :start_time
              AND timestamp <= :end_time
        """)
        count_result = await self.db.execute(count_query, {
            'ref_id': ref_id,
            'start_time': start_time,
            'end_time': end_time
        })
        row = count_result.fetchone()
        stats['count'] = row[0] if row else 0

        return stats

    async def delete_old_data(
        self,
        instance_id: UUID,
        attribute_name: str,
        before_days: int = 30
    ) -> int:
        """删除过期时序数据"""
        ref_id = self.generate_ref_id(instance_id, attribute_name)
        cutoff_date = datetime.utcnow() - timedelta(days=before_days)

        # 先统计数量
        count_query = text("""
            SELECT count(*) FROM timeseries_data
            WHERE ref_id = :ref_id AND timestamp < :cutoff_date
        """)
        count_result = await self.db.execute(count_query, {
            'ref_id': ref_id,
            'cutoff_date': cutoff_date
        })
        row = count_result.fetchone()
        count = row[0] if row else 0

        if count > 0:
            delete_query = text("""
                DELETE FROM timeseries_data
                WHERE ref_id = :ref_id AND timestamp < :cutoff_date
            """)
            await self.db.execute(delete_query, {
                'ref_id': ref_id,
                'cutoff_date': cutoff_date
            })
            await self.db.flush()

        return count