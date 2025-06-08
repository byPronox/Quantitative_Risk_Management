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
            tabIndex={0}
            aria-label={`Select asset ${asset.name}`}
            onKeyDown={e => (e.key === "Enter" ? onSelect(asset.id) : null)}
          >
            <span style={{display: 'flex', alignItems: 'center', gap: '0.7em'}}>
              <span style={{
                display: 'inline-block',
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: selectedId === asset.id ? '#2563eb' : '#cbd5e1',
                marginRight: 8,
                transition: 'background 0.18s'
              }} />
              {asset.name}
            </span>
          </li>
        ))}
      </ul>
    </aside>
  );
}