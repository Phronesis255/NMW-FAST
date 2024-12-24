// src/components/SeoScale.jsx
import React from 'react';

const SeoScale = ({ onBack }) => {
    const handleCsvUpload = (e) => {
        const file = e.target.files[0];
        console.log("Uploaded CSV file:", file);
        // Handle file processing as needed
    };

    return (
        <div className="p-6">
            <h2 className="text-3xl font-bold mb-4">SEO @ SCALE</h2>
            <div className="mb-4">
                <input
                    type="file"
                    accept=".csv"
                    onChange={handleCsvUpload}
                    className="file-input file-input-bordered w-full max-w-xs"
                />
            </div>

            <div className="overflow-x-auto">
                <table className="table w-full">
                    {/* Table head */}
                    <thead>
                        <tr>
                            <th>Column 1</th>
                            <th>Column 2</th>
                            <th>Column 3</th>
                        </tr>
                    </thead>
                    <tbody>
                        {/* Sample rows */}
                        <tr>
                            <td>Data 1</td>
                            <td>Data 2</td>
                            <td>Data 3</td>
                        </tr>
                        <tr>
                            <td>Data A</td>
                            <td>Data B</td>
                            <td>Data C</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <button className="btn btn-secondary mt-4" onClick={onBack}>
                Back
            </button>
        </div>
    );
};

export default SeoScale;
