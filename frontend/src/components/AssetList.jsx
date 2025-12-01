import React from "react";

export default function AssetList({ assets, selectedId, onSelect }) {
  return (
    <aside className="w-full md:w-64 bg-white border-r border-slate-200 flex-shrink-0 md:min-h-[calc(100vh-4rem)]">
      <div className="p-6">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Activos Monitoreados
        </h2>
        <ul className="space-y-2">
          {assets.map(asset => (
            <li
              key={asset.id}
              onClick={() => onSelect(asset.id)}
              tabIndex={0}
              aria-label={`Seleccionar activo ${asset.name}`}
              onKeyDown={e => (e.key === "Enter" ? onSelect(asset.id) : null)}
              className={`
                group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200 outline-none
                ${selectedId === asset.id
                  ? "bg-blue-50 text-blue-700 shadow-sm ring-1 ring-blue-200"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }
              `}
            >
              <span className={`
                w-2.5 h-2.5 rounded-full transition-colors duration-200
                ${selectedId === asset.id ? "bg-blue-600" : "bg-slate-300 group-hover:bg-slate-400"}
              `} />
              <span className="text-sm font-medium">{asset.name}</span>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}