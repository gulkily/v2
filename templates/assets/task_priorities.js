(() => {
  const table = document.querySelector("[data-sortable-table]");
  if (!table) {
    return;
  }

  const tbody = table.tBodies[0];
  const headers = Array.from(table.querySelectorAll("thead th"));
  const status = document.getElementById("task-sort-status");
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  let currentKey = "";
  let currentDirection = "descending";

  const compareValues = (left, right, type) => {
    if (type === "number") {
      return Number.parseFloat(left) - Number.parseFloat(right);
    }
    return collator.compare(left, right);
  };

  const updateHeaderState = (activeKey, direction) => {
    for (const header of headers) {
      const button = header.querySelector(".sort-button");
      if (!button) {
        continue;
      }
      header.setAttribute(
        "aria-sort",
        button.dataset.sortKey === activeKey ? direction : "none"
      );
    }
  };

  const sortRows = (key, type, direction) => {
    const rows = Array.from(tbody.rows);
    rows.sort((leftRow, rightRow) => {
      const leftValue = leftRow.dataset[key] || "";
      const rightValue = rightRow.dataset[key] || "";
      const comparison = compareValues(leftValue, rightValue, type);
      return direction === "ascending" ? comparison : -comparison;
    });
    for (const row of rows) {
      tbody.appendChild(row);
    }
    updateHeaderState(key, direction);
    currentKey = key;
    currentDirection = direction;
    if (status) {
      const directionLabel = direction === "ascending" ? "ascending" : "descending";
      status.textContent = "Sorted by " + key.replace(/_/g, " ") + " " + directionLabel + ".";
    }
  };

  for (const button of table.querySelectorAll(".sort-button")) {
    button.addEventListener("click", () => {
      const key = button.dataset.sortKey;
      const type = button.dataset.sortType || "text";
      let nextDirection;
      if (currentKey === key) {
        nextDirection = currentDirection === "descending" ? "ascending" : "descending";
      } else {
        nextDirection = type === "number" ? "descending" : "ascending";
      }
      sortRows(key, type, nextDirection);
    });
  }
})();
