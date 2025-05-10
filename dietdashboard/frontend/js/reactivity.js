import { reactive, watch as watchVue } from "@vue/reactivity";
// TODO: Batch updates when change multiple checkboxes or part of the state at once

function watch(source, cb, options) {
  return watchVue(source, cb, { ...options, flush: "post", deep: true });
}
export { reactive, watch };
