// src/components/AnalysisResults.jsx
import React, { useState } from 'react';
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
    return (
      <div className="alert alert-error shadow-lg">
        No results to display.
      </div>
    );
  }

  // Prepare TF and Scaled TF-IDF data for the chart
  const tfidfData = results.tfidf_terms || [];
  const chartData = {
    labels: tfidfData.map((term) => term.word),
    datasets: [
      {
        label: 'TF-IDF Scores (Scaled by 100)',
        data: tfidfData.map((term) => term.tfidf_score * 100),
        backgroundColor: 'rgba(34, 139, 34, 0.7)',
        borderColor: 'rgba(34, 139, 34, 1)',
        borderWidth: 1,
      },
      {
        label: 'TF Scores',
        data: tfidfData.map((term) => term.tf_score),
        backgroundColor: 'rgba(255, 140, 0, 0.7)',
        borderColor: 'rgba(255, 140, 0, 1)',
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
        stacked: true,
        title: {
          display: true,
          text: 'Scores (TF + Scaled TF-IDF)',
        },
      },
      x: {
        stacked: true,
      },
    },
  };

  const titles = results.titles || [];
  const urls = results.urls || [];
  const favicons = results.favicons || [];

  // Manage expand/collapse for additional cards
  const [isExpanded, setIsExpanded] = useState(false);

  // Pull the new long-tail keywords data from the backend response
  // This is populated by the code in main.py => final_response.long_tail_keywords
  const longTailKeywords = results.long_tail_keywords || [];

  return (
    <div className="mt-4 space-y-8">
      {/* Top Search Results */}
      <div>
        <h2 className="text-3xl font-bold mb-6 text-primary">
          Top Search Results
        </h2>
        {/* Always show the top 3 cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {titles.slice(0, 3).map((title, index) => (
            <div
              key={index}
              className="card bg-base-100 border border-gray-300 shadow-lg hover:border-primary"
            >
              <div className="card-body flex items-center gap-2">
                <img
                  src={favicons[index]}
                  alt="favicon"
                  className="w-6 h-6 rounded"
                />
                <div>
                  <h3
                    className="card-title text-lg font-bold truncate max-w-[250px]"
                    title={title}
                  >
                    {title}
                  </h3>
                  <a
                    href={urls[index]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 underline text-sm"
                  >
                    {urls[index]}
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Collapsible area for remaining cards */}
        {titles.length > 3 && (
          <div className="collapse collapse-arrow border border-base-300 bg-base-100 rounded-box mt-4">
            <input
              type="checkbox"
              className="peer"
              checked={isExpanded}
              onChange={() => setIsExpanded(!isExpanded)}
            />
            <div className="collapse-title text-xl font-medium">
              {isExpanded ? 'View Less' : 'View More'}
            </div>
            <div className="collapse-content">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-2">
                {titles.slice(3).map((title, index) => (
                  <div
                    key={index + 3}
                    className="card bg-base-100 border border-gray-300 shadow-lg hover:border-primary"
                  >
                    <div className="card-body flex items-center gap-2">
                      <img
                        src={favicons[index + 3]}
                        alt="favicon"
                        className="w-6 h-6 rounded"
                      />
                      <div>
                        <h3
                          className="card-title text-lg font-bold truncate max-w-[250px]"
                          title={title}
                        >
                          {title}
                        </h3>
                        <a
                          href={urls[index + 3]}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-500 underline text-sm"
                        >
                          {urls[index + 3]}
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
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
            <button
              className="btn btn-primary mt-4"
              onClick={() => onGoToHeadingsAnalysis(results.headings_data)}
            >
              Analyze These Headings
            </button>
          </div>
        </div>
      )}

      {/* NEW Long-Tail Keywords Section */}
      {longTailKeywords.length > 0 && (
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="text-3xl font-bold mb-6 text-primary">
              Long-Tail Keywords
            </h2>
            <div className="overflow-x-auto">
              <table className="table table-compact table-zebra w-full">
                <thead className="bg-black text-white">
                  <tr>
                    <th>Keyword</th>
                    <th>Relevance Score</th>
                    <th>Frequency</th>
                    <th>KW Length</th>
                  </tr>
                </thead>
                <tbody>
                  {longTailKeywords.map((item, index) => (
                    <tr key={index} className="hover">
                      <td>{item.keyword}</td>
                      <td>{item.relevanceScore}</td>
                      <td>{item.frequency}</td>
                      <td>{item.kwLength}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisResults;
