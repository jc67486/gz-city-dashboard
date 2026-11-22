<template>
  <section class="panel">
    <header class="panel__head">
      <span class="panel__bar"></span>
      <h3 class="panel__title">{{ title }}</h3>
      <span v-if="sub" class="panel__sub">{{ sub }}</span>
      <span class="panel__line"></span>
    </header>
    <div class="panel__body">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  sub: { type: String, default: '' }
})
</script>

<style scoped>
.panel {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: linear-gradient(180deg, rgba(14, 32, 66, 0.82), rgba(8, 18, 38, 0.72));
  border: 1px solid rgba(64, 158, 255, 0.28);
  border-radius: 4px;
  box-shadow: inset 0 0 26px rgba(0, 132, 255, 0.14);
}
.panel::before,
.panel::after {
  content: '';
  position: absolute;
  width: 10px;
  height: 10px;
  border: 2px solid #00d4ff;
  opacity: 0.85;
}
.panel::before { top: -1px; left: -1px; border-right: 0; border-bottom: 0; }
.panel::after { bottom: -1px; right: -1px; border-left: 0; border-top: 0; }

.panel__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 8px;
  flex: none;
}
.panel__bar {
  width: 3px;
  height: 14px;
  background: linear-gradient(180deg, #00d4ff, #1d6fff);
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.8);
}
.panel__title {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: #e8f4ff;
}
.panel__sub {
  font-size: 12px;
  color: #6f9dc9;
  letter-spacing: 0.5px;
}
.panel__line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(0, 212, 255, 0.55), rgba(0, 212, 255, 0));
}
.panel__body {
  flex: 1;
  min-height: 0;
  padding: 0 10px 10px;
}
</style>
