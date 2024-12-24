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

const EditorComponent = ({ tfidfTerms = [], targetScores = {}, onChange }) => {
    const editorInstance = useRef(null);
    const [editorContent, setEditorContent] = useState(""); 
    const [termOccurrences, setTermOccurrences] = useState({}); 
    const [optimizationScore, setOptimizationScore] = useState(0);
    const [termMetrics, setTermMetrics] = useState([]);

    const computeTermMetrics = (terms, scores, content) => {
        const wordCount = content.split(/\s+/).filter(Boolean).length || 1;
        return terms.map((term) => {
            const avgTfScore = scores[term] || 0;
            const target = Math.floor(avgTfScore); // directly use tf_score
            const delta = Math.max(1, Math.floor(target * 0.1));
            const minOccurrences = Math.max(1, target - delta);
            const maxOccurrences = target + delta;
            return { term, target, minOccurrences, maxOccurrences };
        });
    };

    useEffect(() => {
        if (!editorInstance.current) {
            // Initialize Editor.js with heading and other blocks enabled
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
                            defaultStyle: 'unordered'
                        }
                    }
                },
                data: {
                    time: new Date().getTime(),
                    blocks: [
                        {
                            type: 'paragraph',
                            data: {
                                text: '',
                            },
                        },
                    ],
                },
                onChange: async () => {
                    try {
                        const outputData = await editorInstance.current.save();
                        const textContent = outputData.blocks
                            .map((block) => block.data.text || "")
                            .join(" ");
                        console.log("[DEBUG] Editor Content Updated:", textContent); 
                        setEditorContent(textContent);
                    } catch (error) {
                        console.error("Error saving Editor.js data:", error);
                    }
                },
            });
        }

        return () => {
            if (editorInstance.current && typeof editorInstance.current.destroy === "function") {
                editorInstance.current.destroy();
                editorInstance.current = null;
            }
        };
    }, []);

    // Call parent's onChange whenever editorContent updates
    useEffect(() => {
        if (onChange) {
            console.log("[DEBUG] Triggering onChange Callback");
            onChange(editorContent);
        }
    }, [editorContent, onChange]);

    useEffect(() => {
        if (editorContent && tfidfTerms.length > 0) {
            console.log("[DEBUG] Processing TF-IDF Terms:", tfidfTerms);
            console.log("[DEBUG] Target Scores:", targetScores);

            const occurrences = {};
            tfidfTerms.forEach((term) => {
                const regex = new RegExp(`\\b${term}\\b`, "gi");
                occurrences[term] = (editorContent.match(regex) || []).length;
            });

            console.log("[DEBUG] Term Occurrences:", occurrences);
            setTermOccurrences(occurrences);

            const metrics = computeTermMetrics(tfidfTerms, targetScores, editorContent);
            setTermMetrics(metrics);

            const score = calculateOptimizationScore(occurrences, metrics);
            console.log("[DEBUG] Optimization Score Calculated:", score);
            setOptimizationScore(score);
        } else {
            setTermOccurrences({});
            setTermMetrics([]);
            setOptimizationScore(0);
        }
    }, [editorContent, tfidfTerms, targetScores]);

    const calculateOptimizationScore = (occurrences, metrics) => {
        let totalScore = 0;
        let maxScore = 0;

        metrics.forEach(({ term, target }) => {
            const actual = occurrences[term] || 0;
            totalScore += Math.min(actual, target);
            maxScore += target;
        });

        const score = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;
        console.log(`[DEBUG] Total Score: ${totalScore}, Max Score: ${maxScore}, Final Score: ${score}`);
        return score;
    };

    const metricsByTerm = termMetrics.reduce((acc, m) => {
        acc[m.term] = m;
        return acc;
    }, {});

    const chartData = {
        labels: tfidfTerms,
        datasets: [
            {
                label: "Target Occurrences",
                data: tfidfTerms.map((term) => (metricsByTerm[term]?.target || 0)),
                backgroundColor: "rgba(75, 192, 192, 0.6)",
            },
            {
                label: "Actual Occurrences",
                data: tfidfTerms.map((term) => termOccurrences[term] || 0),
                backgroundColor: "rgba(255, 99, 132, 0.6)",
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: "top",
            },
            title: {
                display: true,
                text: "TF-IDF Term Analysis",
            },
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };

    return (
        <div className="flex flex-col md:flex-row gap-6">
            {/* Sidebar for TF-IDF Terms */}
            <div className="w-full md:w-1/3 bg-gray-100 p-4 rounded-lg shadow">
                <h2 className="text-xl font-bold mb-4">TF-IDF Terms</h2>
                <ul>
                    {tfidfTerms.map((term) => {
                        const { target = 0, minOccurrences = 0, maxOccurrences = 0 } = metricsByTerm[term] || {};
                        const actual = termOccurrences[term] || 0;
                        return (
                            <li key={term} className="mb-2">
                                <div className="flex justify-between">
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

            {/* Editor and Chart Section */}
            <div className="w-full md:w-2/3 flex flex-col gap-6">
                {/* Editor with fixed dimensions and basic heading styling */}
                <div 
                    id="editorjs" 
                    className="border rounded-lg p-4 bg-white shadow-md"
                    style={{
                        minHeight: '400px',
                        maxHeight: '600px',
                        overflowY: 'auto',
                        width: '100%',
                        // Add basic styling so you can see heading differences visually
                    }}
                >
                    <style>
                        {`
                            .ce-block__content h1 {
                                font-size: 1.5em;
                                font-weight: bold;
                                margin-bottom: 0.5em;
                            }
                            .ce-block__content h2 {
                                font-size: 1.4em;
                                font-weight: bold;
                                margin-bottom: 0.5em;
                            }
                            .ce-block__content h3 {
                                font-size: 1.3em;
                                font-weight: bold;
                                margin-bottom: 0.5em;
                            }
                            .ce-block__content h4 {
                                font-size: 1.2em;
                                font-weight: bold;
                                margin-bottom: 0.5em;
                            }
                        `}
                    </style>
                </div>

                {/* Optimization Score */}
                <div className="text-center">
                    <h2 className="text-xl font-bold">Optimization Score</h2>
                    <div className="text-3xl font-bold text-green-500">{optimizationScore}%</div>
                </div>

                {/* Chart */}
                <div>
                    <Bar data={chartData} options={chartOptions} />
                </div>
            </div>
        </div>
    );
};

export default EditorComponent;
