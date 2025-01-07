import React from 'react';

const HomePage = ({ onSelect }) => {
    return (
        <div className="flex flex-col justify-center items-center h-screen">
            <h1 className="text-4xl font-bold mb-12 text-secondary-content">What are we making today?</h1>
            <div 
                className="card w-96 bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-xl mb-4 cursor-pointer transform transition-transform hover:scale-105" 
                onClick={() => onSelect('generate')}
            >
                <div className="card-body">
                    <h2 className="card-title text-2xl font-bold">Generate a New Article</h2>
                    <p className="text-lg">Create a new article from scratch.</p>
                </div>
            </div>
            <div 
                className="card w-96 bg-gradient-to-r from-green-500 to-teal-500 text-white shadow-xl cursor-pointer transform transition-transform hover:scale-105" 
                onClick={() => onSelect('optimize')}
            >
                <div className="card-body">
                    <h2 className="card-title text-2xl font-bold">Optimize Existing Article</h2>
                    <p className="text-lg">Optimize an existing article for SEO.</p>
                </div>
            </div>
        </div>
    );
};

export default HomePage;