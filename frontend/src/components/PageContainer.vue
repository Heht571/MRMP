<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div v-if="title || $slots.extra" class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold tracking-tight text-gray-900">{{ title }}</h2>
        <p v-if="description" class="mt-1 text-sm text-gray-500">{{ description }}</p>
      </div>
      <div v-if="$slots.extra" class="flex items-center gap-3">
        <slot name="extra"></slot>
      </div>
    </div>

    <!-- Main Content -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-md">
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
