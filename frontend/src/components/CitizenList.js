import React, { useEffect } from 'react';

const CitizenList = ({ citizens, loading, onRefresh }) => {
  useEffect(() => {
    // Load citizens when component mounts
    onRefresh();
  }, [onRefresh]);

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>Loading citizens...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="header-section">
        <h2>Citizen Records</h2>
        <button className="btn" onClick={onRefresh}>
          Refresh
        </button>
      </div>

      {citizens.length === 0 ? (
        <p>No citizen records found.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>ID Number</th>
              <th>Date of Birth</th>
              <th>Phone</th>
              <th>Address</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {citizens.map((citizen) => (
              <tr key={citizen.id}>
                <td>{citizen.id}</td>
                <td>{citizen.prefix} {citizen.first_name} {citizen.last_name}</td>
                <td>{citizen.cid || 'N/A'}</td>
                <td>{citizen.dob || 'N/A'}</td>
                <td>{citizen.phone || 'N/A'}</td>
                <td>{citizen.address_full || 'N/A'}</td>
                <td>
                  <span className={`status status-${citizen.status}`}>
                    {citizen.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default CitizenList;