<template>
  <div class="page-container">
    <!-- Page Header -->
    <div v-if="title || $slots.extra" class="page-header">
      <div class="header-content">
        <h2 class="page-title">{{ title }}</h2>
        <p v-if="description" class="page-description">{{ description }}</p>
      </div>
      <div v-if="$slots.extra" class="header-actions">
        <slot name="extra"></slot>
      </div>
    </div>

    <!-- Main Content -->
    <div class="page-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>

<style scoped>
.page-container {
  padding: var(--space-lg);
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

@media (min-width: 640px) {
  .page-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-dark);
  letter-spacing: -0.01em;
  margin: 0;
}

.page-description {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.page-content {
  background: var(--color-surface-light);
  border-radius: var(--radius-xl);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  transition: box-shadow var(--transition-base);
}

.page-content:hover {
  box-shadow: var(--shadow-card);
}
</style>