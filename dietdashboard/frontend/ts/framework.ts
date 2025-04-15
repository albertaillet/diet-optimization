export { F, h };

function h(tag: string | Function, props: any, ...children: any[]): HTMLElement | Text {
  if (typeof tag === "function") {
    return tag({ ...props, children });
  }
  const el = document.createElement(tag);
  if (props) {
    for (const key in props) {
      if (key.startsWith("on") && typeof props[key] === "function") {
        el.addEventListener(key.substring(2).toLowerCase(), props[key]);
      } else if (key === "className") {
        el.setAttribute("class", props[key]);
      } else if (key === "style" && typeof props[key] === "object") {
        Object.assign(el.style, props[key]);
      } else if (key !== "children") {
        el.setAttribute(key, props[key]);
      }
    }
  }
  const appendChild = (child: any) => {
    if (typeof child === "string" || typeof child === "number") {
      el.appendChild(document.createTextNode(child.toString()));
    } else if (child instanceof Node) {
      el.appendChild(child);
    }
  };
  children.forEach(child => {
    if (Array.isArray(child)) {
      child.forEach(nestedChild => appendChild(nestedChild));
    } else {
      appendChild(child);
    }
  });
  return el;
}

// Fragment component
function F({ children }: { children: Node[] }): DocumentFragment {
  const fragment = document.createDocumentFragment();
  children.forEach(child => {
    if (Array.isArray(child)) {
      child.forEach(nestedChild => fragment.appendChild(nestedChild));
    } else {
      fragment.appendChild(child);
    }
  });
  return fragment;
}
