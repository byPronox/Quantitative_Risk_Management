import React, { useEffect, useState } from "react";
import { fetchNvdVulnerabilities } from "../services/nvd";

export default function NvdPage() {
  const [keyword, setKeyword] = useState("react");
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await fetchNvdVulnerabilities(keyword);
      setVulnerabilities(data.vulnerabilities || []);
    } catch (error) {
      console.error("Error fetching NVD data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div className="nvd-page">
      <h2>Buscar Vulnerabilidades NVD</h2>
      <input
        type="text"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        placeholder="Buscar por palabra clave"
      />
      <button onClick={handleSearch}>Buscar</button>

      {loading ? (
        <p>Cargando...</p>
      ) : (
        <ul>
          {vulnerabilities.map((vuln, idx) => (
            <li key={idx}>
              <strong>{vuln.cve.id}</strong> - {vuln.cve.descriptions[0]?.value}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
