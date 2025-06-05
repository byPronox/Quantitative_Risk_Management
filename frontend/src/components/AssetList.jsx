import React from "react";

export default function AssetList({ assets, selectedId, onSelect }) {
  return (
    <aside className="asset-list">
      <h2>Assets</h2>
      <ul>
        {assets.map(asset => (
          <li
            key={asset.id}
            className={selectedId === asset.id ? "selected" : ""}
            onClick={() => onSelect(asset.id)}
          >
            {asset.name}
          </li>
        ))}
      </ul>
    </aside>
  );
}