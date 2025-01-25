// src/components/AnalysisResults.jsx
import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

const AnalysisResults = ({ results, onGoToEditor, onGoToHeadingsAnalysis }) => {
    if (!results) {
        return <div className="alert alert-error shadow-lg">No results to display.</div>;
    }

    // Prepare TF and Scaled TF-IDF data for the chart
    const tfidfData = results.tfidf_terms || [];
    const chartData = {
        labels: tfidfData.map((term) => term.word),
        datasets: [
            {
                label: 'TF-IDF Scores (Scaled by 100)',
                data: tfidfData.map((term) => term.tfidf_score * 100), // Scaled TF-IDF scores
                backgroundColor: 'rgba(34, 139, 34, 0.7)', // Dark Green
                borderColor: 'rgba(34, 139, 34, 1)',       // Solid Dark Green
                borderWidth: 1,
            },
            {
                label: 'TF Scores',
                data: tfidfData.map((term) => term.tf_score),
                backgroundColor: 'rgba(255, 140, 0, 0.7)', // Dark Orange
                borderColor: 'rgba(255, 140, 0, 1)',       // Solid Orange
                borderWidth: 1,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                stacked: true, // Enable stacking
                title: {
                    display: true,
                    text: 'Scores (TF + Scaled TF-IDF)',
                },
            },
            x: {
                stacked: true, // Enable stacking
            },
        },
    };

    return (
        <div className="mt-4 space-y-8">
            {/* Top Search Results */}
            <div>
                <h2 className="text-3xl font-bold mb-6 text-primary">Top Search Results</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {results.titles.map((title, index) => (
                        <div
                            key={index}
                            className="card bg-base-100 border border-gray-300 shadow-lg hover:border-primary"
                        >
                            <div className="card-body flex items-center gap-2">
                                <img
                                    src={results.favicons[index]}
                                    alt="favicon"
                                    className="w-6 h-6 rounded"
                                />
                                <div>
                                    <h3 className="card-title text-lg font-bold">{title}</h3>
                                    <a
                                        href={results.urls[index]}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-500 underline text-sm"
                                    >
                                        {results.urls[index]}
                                    </a>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* TF-IDF and TF Chart and Table Side-by-Side */}
            {tfidfData.length > 0 && (
                <div className="card bg-base-100 shadow-xl">
                    <div className="card-body">
                        <h2 className="text-3xl font-bold mb-6 text-primary">
                            Top TF and TF-IDF Terms
                        </h2>
                        <div className="flex flex-col md:flex-row gap-4 h-[400px]">
                            {/* Bar Chart */}
                            <div className="w-full md:w-1/2 flex items-center">
                                <div className="h-full w-full">
                                    <Bar data={chartData} options={chartOptions} />
                                </div>
                            </div>

                            {/* TF-IDF Table */}
                            <div className="w-full md:w-1/2 overflow-x-auto">
                                <table className="table table-zebra table-compact w-full h-full">
                                    <thead className="bg-black text-primary">
                                        <tr>
                                            <th>Rank</th>
                                            <th>Term</th>
                                            <th>TF Score</th>
                                            <th>TF-IDF Score (Scaled)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {tfidfData.map((term, index) => (
                                            <tr key={index} className="hover">
                                                <td>{index + 1}</td>
                                                <td>{term.word}</td>
                                                <td>{term.tf_score.toFixed(3)}</td>
                                                <td>{(term.tfidf_score * 100).toFixed(3)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Headings Section */}
            {results.headings_data && results.headings_data.length > 0 && (
                <div className="card bg-base-100 shadow-xl">
                    <div className="card-body">
                        <h2 className="text-3xl font-bold mb-6 text-primary">Headings</h2>
                        <div className="overflow-x-auto">
                            <table className="table table-compact table-zebra w-full">
                                <thead className="bg-black text-white">
                                    <tr>
                                        <th>#</th>
                                        <th>Heading</th>
                                        <th>Source</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {results.headings_data.map((heading, index) => (
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
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {/* NEW BUTTON to go to separate headings analysis screen */}
                        <button
                            className="btn btn-primary mt-4"
                            onClick={() => onGoToHeadingsAnalysis(results.headings_data)}
                        >
                            Analyze These Headings
                        </button>

                    </div>
                </div>
            )}
        </div>
    );
};

export default AnalysisResults;
