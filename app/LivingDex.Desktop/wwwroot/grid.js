// The two things the dex grid's keyboard cursor needs a browser for.
//
// The grid is one tab stop holding a cursor, rather than two thousand focusable buttons, and
// that is not only about tab stops: `Virtualize` only renders the rows it is scrolling past, so
// the tile a player is moving towards does not exist yet and cannot be focused. The focus stays
// on the grid, `aria-activedescendant` names the current cell, and what has to happen here is
// scrolling that cell into view and stopping the browser scrolling on its own.
window.livingdex = window.livingdex || {};

(function () {
  const ours = new Set([
    "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
    "Home", "End", "PageUp", "PageDown",
    "Enter", " ", "Spacebar",
  ]);

  // A reference to an element that has not been drawn yet arrives as a plain object rather
  // than as the element, so each of these checks for what it is about to use.
  const drawn = (element) => Boolean(element) && element.nodeType === 1;

  // Blazor's own keydown handler is a second listener and still runs; this one stops the
  // browser acting on the same key - scrolling the grid out from under the cursor we are about
  // to move, or, when a click has left the focus on a tile's own button, pressing that button
  // as well as doing what the grid says the key means. Inside the grid these keys belong to the
  // grid. Tab is deliberately not in the list: a keyboard user has to be able to leave.
  window.livingdex.gridKeys = function (element) {
    if (!drawn(element) || element.dataset.gridKeys) {
      return false;
    }

    element.dataset.gridKeys = "on";
    element.addEventListener("keydown", function (event) {
      if (ours.has(event.key)) {
        event.preventDefault();
      }
    });

    return true;
  };

  // Scrolled by row rather than by element, for the same reason: the row may not be rendered.
  window.livingdex.showRow = function (element, row, rowHeight) {
    if (!drawn(element)) {
      return;
    }

    const top = row * rowHeight;
    const bottom = top + rowHeight;

    if (top < element.scrollTop) {
      element.scrollTop = top;
    } else if (bottom > element.scrollTop + element.clientHeight) {
      element.scrollTop = bottom - element.clientHeight;
    }
  };

  // Clicking a tile presses a button inside it, and a tick redraws that tile - which can take
  // the focused button away with it and leave the keyboard with nothing. So every click hands
  // the focus back to the grid, which is where the cursor lives and which no tile can redraw.
  window.livingdex.focusGrid = function (element) {
    if (drawn(element)) {
      element.focus({ preventScroll: true });
    }
  };

  // How many tiles fit across, and a call back whenever that changes.
  //
  // The count has to be worked out here and sent to C# rather than left to CSS, because the
  // rows are chunked in C# for `Virtualize` and the keyboard counts in columns. `clientWidth`
  // already leaves out the scrollbar and takes in the padding, so the padding comes off.
  const columnsFor = (element, tile, gap, padding) => {
    const usable = element.clientWidth - (2 * padding);
    return Math.max(1, Math.floor((usable + gap) / (tile + gap)));
  };

  window.livingdex.watchColumns = function (element, tile, gap, padding, caller) {
    if (!drawn(element) || element.dataset.columnsWatched) {
      return 0;
    }

    element.dataset.columnsWatched = "on";
    let last = columnsFor(element, tile, gap, padding);

    // Observing the grid rather than the window: the sidebar and the scrollbar change this
    // width without the window moving at all. The observer is held on the element, so it goes
    // when the element does and there is nothing to unregister.
    element.livingdexColumns = new ResizeObserver(function () {
      const now = columnsFor(element, tile, gap, padding);

      if (now !== last) {
        last = now;
        caller.invokeMethodAsync("ColumnsChanged", now);
      }
    });

    element.livingdexColumns.observe(element);

    return last;
  };

  // What a page means here, asked rather than assumed: the window can be any height.
  window.livingdex.rowsVisible = function (element, rowHeight) {
    if (!drawn(element) || !rowHeight) {
      return 1;
    }

    return Math.max(1, Math.floor(element.clientHeight / rowHeight));
  };
})();
