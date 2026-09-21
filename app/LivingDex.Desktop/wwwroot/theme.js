// Applying the theme has to touch <html>, which sits outside the Blazor root component, so it
// happens here rather than in a component's markup.
window.livingdex = window.livingdex || {};

window.livingdex.applyTheme = function (theme) {
  var root = document.documentElement;

  if (theme === 'system') {
    // Absent rather than empty: the CSS keys off whether the attribute is there at all.
    delete root.dataset.theme;
  } else {
    root.dataset.theme = theme;
  }

  // The caller needs to know what the player is actually looking at, not just what they chose:
  // toggling away from "system" has to land on the opposite of what is on screen.
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  return theme;
};
