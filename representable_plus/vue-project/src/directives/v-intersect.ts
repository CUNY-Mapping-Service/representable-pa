import type { DirectiveBinding } from 'vue'

type Callback = (entry: IntersectionObserverEntry, el: Element) => void
type Options = IntersectionObserverInit
type Value =
  | Callback
  | {
      callback: Callback
      options?: Options
      once?: boolean
    }

interface ElWithObserver extends Element {
  __vIntersectObserver?: IntersectionObserver
}

export default {
  mounted(el: ElWithObserver, binding: DirectiveBinding<Value>) {
    const val = binding.value
    const callback: Callback | undefined = typeof val === 'function' ? val : val?.callback
    const options: Options = (typeof val === 'object' && val?.options) || {
      root: null,
      rootMargin: '0px',
      threshold: 0.1,
    }
    const once = (typeof val === 'object' && val?.once) ?? true

    if (typeof callback !== 'function') return

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          callback(entry, el)
          if (once) obs.unobserve(entry.target)
        }
      })
    }, options)

    el.__vIntersectObserver = observer
    observer.observe(el)
  },

  unmounted(el: ElWithObserver) {
    if (el.__vIntersectObserver) {
      el.__vIntersectObserver.disconnect()
      delete el.__vIntersectObserver
    }
  },
}
