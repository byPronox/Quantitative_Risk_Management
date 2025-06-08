import React, { useEffect, useState } from "react";
import { fetchNvdVulnerabilities } from "../services/nvd";

export default function NvdPage() {
  const [keyword, setKeyword] = useState("react");
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchNvdVulnerabilities(keyword);
      setVulnerabilities(data.vulnerabilities || []);
    } catch (error) {
      setError("Error fetching NVD data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
    // eslint-disable-next-line
  }, []);

  return (
    <div className="nvd-page">
      <h2>Search NVD Vulnerabilities</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
        style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 18,
        }}
      >
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Search by keyword (e.g. react)"
          style={{ minWidth: 180 }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{ marginLeft: 8 }}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>
      {error && (
        <p style={{ color: "#ef4444", fontWeight: 600 }}>{error}</p>
      )}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <ul>
          {vulnerabilities.length === 0 && (
            <li>No vulnerabilities found.</li>
          )}
          {vulnerabilities.map((vuln, idx) => (
            <li key={idx}>
              <strong>{vuln.cve.id}</strong>
              {vuln.cve.descriptions[0]?.value && (
                <span
                  style={{
                    display: "block",
                    marginTop: 6,
                    color: "#475569",
                    fontSize: "0.98rem",
                  }}
                >
                  {vuln.cve.descriptions[0]?.value}
                </span>
              )}
              {vuln.cve.published && (
                <span
                  style={{
                    display: "block",
                    marginTop: 4,
                    fontSize: "0.93rem",
                    color: "#64748b",
                  }}
                >
                  Published:{" "}
                  {new Date(vuln.cve.published).toLocaleDateString()}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
