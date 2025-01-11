import React, { useEffect, useRef, useState } from 'react';
import EditorJS from '@editorjs/editorjs';
import Header from '@editorjs/header';
import Paragraph from '@editorjs/paragraph';
import List from '@editorjs/list';
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

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const EditorComponent = ({
  initialContent,
  tfidfTerms = [],
  targetScores = {},
  onChange,
}) => {
  const editorInstance = useRef(null);
  const [editorContent, setEditorContent] = useState(initialContent || '');
  const [termOccurrences, setTermOccurrences] = useState({});
  const [optimizationScore, setOptimizationScore] = useState(0);
  const [termMetrics, setTermMetrics] = useState([]);

  // -- Utility function to compute term metrics dynamically --
  const computeTermMetrics = (terms, scores, content) => {
    const wordCount = content.split(/\s+/).filter(Boolean).length || 1;
    return terms.map((term) => {
      // Here you multiply user wordCount to get the target for the user's actual doc length
      const rawTarget = (scores[term] || 0) * wordCount;
      const target = Math.floor(rawTarget);

      const delta = Math.max(1, Math.floor(target * 0.1));
      const minOccurrences = Math.max(1, target - delta);
      const maxOccurrences = target + delta;
      return { term, target, minOccurrences, maxOccurrences };
    });
  };

  // -- Initialize Editor.js only once --
  useEffect(() => {
    if (!editorInstance.current) {
      editorInstance.current = new EditorJS({
        holder: 'editorjs',
        autofocus: true,
        placeholder: 'Start typing your content here...',
        tools: {
          header: {
            class: Header,
            inlineToolbar: ['bold', 'italic', 'link'],
            config: {
              placeholder: 'Enter a heading',
              levels: [1, 2, 3, 4],
              defaultLevel: 1,
            },
          },
          paragraph: {
            class: Paragraph,
            inlineToolbar: ['bold', 'italic', 'link'],
            config: {
              placeholder: 'Start typing here...',
            },
          },
          list: {
            class: List,
            inlineToolbar: ['bold', 'italic', 'link'],
            config: {
              defaultStyle: 'unordered',
            },
          },
        },
        data: {
          time: new Date().getTime(),
          blocks: [
            {
              type: 'paragraph',
              data: {
                text: initialContent || '',
              },
            },
          ],
        },
        onChange: async () => {
          try {
            const outputData = await editorInstance.current.save();
            const textContent = outputData.blocks
              .map((block) => block.data.text || '')
              .join(' ');
            console.log('[DEBUG] Editor Content Updated:', textContent);
            setEditorContent(textContent);
          } catch (error) {
            console.error('Error saving Editor.js data:', error);
          }
        },
      });
    }

    return () => {
      if (
        editorInstance.current &&
        typeof editorInstance.current.destroy === 'function'
      ) {
        editorInstance.current.destroy();
        editorInstance.current = null;
      }
    };
  }, [initialContent]);

  // -- Propagate editorContent changes to parent (App.jsx) --
  useEffect(() => {
    if (onChange) {
      console.log('[DEBUG] Triggering onChange Callback');
      onChange(editorContent);
    }
  }, [editorContent, onChange]);

  // -- Recompute metrics and occurrences whenever editorContent or tfidfTerms change --
  useEffect(() => {
    if (editorContent && tfidfTerms.length > 0) {
      console.log('[DEBUG] Processing TF-IDF Terms:', tfidfTerms);
      console.log('[DEBUG] Target Scores:', targetScores);

      // Count actual occurrences
      const occurrences = {};
      tfidfTerms.forEach((term) => {
        const regex = new RegExp(`\\b${term}\\b`, 'gi');
        occurrences[term] = (editorContent.match(regex) || []).length;
      });
      setTermOccurrences(occurrences);

      // Recompute min/max/target for each term
      const metrics = computeTermMetrics(tfidfTerms, targetScores, editorContent);
      setTermMetrics(metrics);

      // Calculate overall optimization score
      const score = calculateOptimizationScore(occurrences, metrics);
      console.log('[DEBUG] Optimization Score Calculated:', score);
      setOptimizationScore(score);
    } else {
      setTermOccurrences({});
      setTermMetrics([]);
      setOptimizationScore(0);
    }
  }, [editorContent, tfidfTerms, targetScores]);

  // -- Compute an aggregate “optimization score” based on how many times terms appear --
  const calculateOptimizationScore = (occurrences, metrics) => {
    let totalScore = 0;
    let maxScore = 0;

    metrics.forEach(({ term, target }) => {
      const actual = occurrences[term] || 0;
      totalScore += Math.min(actual, target);
      maxScore += target;
    });

    const score = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;
    console.log(
      `[DEBUG] Total Score: ${totalScore}, Max Score: ${maxScore}, Final Score: ${score}`
    );
    return score;
  };

  // -- For chart data --
  const metricsByTerm = termMetrics.reduce((acc, m) => {
    acc[m.term] = m;
    return acc;
  }, {});

  const chartData = {
    labels: tfidfTerms,
    datasets: [
      {
        label: 'Target Occurrences',
        data: tfidfTerms.map((term) => metricsByTerm[term]?.target || 0),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
      {
        label: 'Actual Occurrences',
        data: tfidfTerms.map((term) => termOccurrences[term] || 0),
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'TF-IDF Term Analysis',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 w-full">
      {/* TF-IDF Terms side panel (DaisyUI card) */}
      <div className="card bg-base-100 shadow-xl w-full md:w-1/3">
        <div className="card-body">
          <h2 className="card-title">TF-IDF Terms</h2>
          <ul className="space-y-3">
            {tfidfTerms.map((term) => {
              const { target = 0, minOccurrences = 0, maxOccurrences = 0 } =
                metricsByTerm[term] || {};
              const actual = termOccurrences[term] || 0;
              return (
                <li key={term}>
                  <div className="flex justify-between font-bold">
                    <span>{term}</span>
                    <span>
                      {actual}/{target} ({minOccurrences}-{maxOccurrences})
                    </span>
                  </div>
                  <progress
                    className="progress progress-primary w-full"
                    value={actual}
                    max={maxOccurrences}
                  ></progress>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      {/* Main editor + chart area (DaisyUI card) */}
      <div className="card bg-base-100 shadow-xl w-full md:w-2/3 flex flex-col">
        <div className="card-body flex flex-col gap-4">
          {/* Editor Container with fixed height/width */}
          <div
            className="border border-base-300 rounded-lg bg-white shadow-md
                       overflow-y-auto overflow-x-hidden
                       mx-auto p-2"
            style={{
              width: '800px',     // <-- fixed width
              maxWidth: '100%',   // ensure it doesn't exceed the screen
              height: '550px',    // fixed height
              whiteSpace: 'pre-wrap',
            }}
          >
            <div
              id="editorjs"
              className="w-full h-full"
              style={{
                // any extra style to avoid horizontal expansion
              }}
            ></div>
          </div>

          {/* Optimization Score */}
          <div className="text-center">
            <h2 className="text-xl font-bold">Optimization Score</h2>
            <div className="text-3xl font-bold text-green-500">
              {optimizationScore}%
            </div>
          </div>

          {/* Chart.js Bar Chart */}
          <div className="h-72 md:h-64">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditorComponent;
