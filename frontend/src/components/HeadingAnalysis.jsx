// src/components/HeadingAnalysis.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const HeadingAnalysis = ({ headings, onBack }) => {
  const [backendMessage, setBackendMessage] = useState('');

  useEffect(() => {
    // Call the new dummy endpoint when this component mounts
    const fetchDummyData = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/headings-analyze');
        setBackendMessage(res.data.message || 'No message received');
      } catch (err) {
        console.error('[DEBUG] Error calling /api/headings-analyze:', err);
        setBackendMessage('Error calling backend');
      }
    };

    fetchDummyData();
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Heading Analysis</h2>

      {/* Display the dummy message from backend */}
      <p className="text-gray-600 mb-6">{backendMessage}</p>

      {/* Table of headings */}
      <table className="table table-zebra table-compact w-full">
        <thead className="bg-black text-white">
          <tr>
            <th>#</th>
            <th>Heading</th>
            <th>URL</th>
            <th>Title</th>
          </tr>
        </thead>
        <tbody>
          {headings.map((heading, index) => (
            <tr key={index} className="hover">
              <td>{index + 1}</td>
              <td>{heading.text}</td>
              <td>
                <a
                  href={heading.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 underline text-sm"
                >
                  {heading.url}
                </a>
              </td>
              <td>{heading.title}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Back button */}
      <button
        className="btn btn-secondary mt-4"
        onClick={onBack}
      >
        Back
      </button>
    </div>
  );
};

export default HeadingAnalysis;
