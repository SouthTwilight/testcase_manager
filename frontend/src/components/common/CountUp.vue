<template>
  <span ref="countRef">{{ displayValue }}</span>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { easeOutCubic } from '../../utils/easing'

const props = defineProps({
  endValue: {
    type: Number,
    required: true
  },
  duration: {
    type: Number,
    default: 2
  },
  decimals: {
    type: Number,
    default: 0
  },
  prefix: {
    type: String,
    default: ''
  },
  suffix: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['complete'])

const displayValue = ref('')
const animationFrame = ref(null)
const startTime = ref(null)
const startValue = ref(0)

const formatNumber = (num) => {
  return num.toFixed(props.decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const animate = (timestamp) => {
  if (!startTime.value) startTime.value = timestamp

  const progress = timestamp - startTime.value
  const percentage = Math.min(progress / (props.duration * 1000), 1)
  const eased = easeOutCubic(percentage)

  const currentValue = startValue.value + (props.endValue - startValue.value) * eased

  displayValue.value = `${props.prefix}${formatNumber(currentValue)}${props.suffix}`

  if (percentage < 1) {
    animationFrame.value = requestAnimationFrame(animate)
  } else {
    emit('complete')
  }
}

const startAnimation = () => {
  startValue.value = parseFloat(displayValue.value.replace(/[^0-9.-]/g, '')) || 0
  startTime.value = null

  if (animationFrame.value) {
    cancelAnimationFrame(animationFrame.value)
  }

  animationFrame.value = requestAnimationFrame(animate)
}

onMounted(() => {
  displayValue.value = `${props.prefix}${formatNumber(0)}${props.suffix}`
  setTimeout(startAnimation, 100)
})

onUnmounted(() => {
  if (animationFrame.value) {
    cancelAnimationFrame(animationFrame.value)
  }
})

watch(() => props.endValue, () => {
  startAnimation()
})
</script>
