<template>
  <footer v-if="$slidev.nav.currentPage > 0" class="slide-counter">
    {{ $slidev.nav.currentPage }}/{{ $slidev.nav.total }}
  </footer>
</template>

<style>
.slidev-layout {
  color: #000 !important;
  background: #fff !important;
}

.slidev-layout h1,
.slidev-layout h2,
.slidev-layout h3,
.slidev-layout p,
.slidev-layout li,
.slidev-layout td,
.slidev-layout th,
.slidev-layout a {
  color: #000 !important;
}

.slide-counter {
  position: fixed;
  right: 1.5rem;
  bottom: 1rem;
  font-size: 0.75rem;
  color: #000;
  z-index: 100;
}
</style>
