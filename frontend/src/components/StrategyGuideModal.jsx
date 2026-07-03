import React, { useState, useEffect } from 'react';
import { X, BookOpen, Calculator, Play, Target, LogOut, CheckCircle2 } from 'lucide-react';
import { STRATEGY_EXPLANATIONS, DEFAULT_EXPLANATION } from '../data/strategyExplanations';
import '../index.css';

export default function StrategyGuideModal({ isOpen, onClose, strategyKey, strategyName }) {
    const [language, setLanguage] = useState('English');
    const [isVisible, setIsVisible] = useState(false);

    // Handle fade-in/out transitions
    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
        } else {
            const timer = setTimeout(() => setIsVisible(false), 300); // 300ms matches css transition
            return () => clearTimeout(timer);
        }
    }, [isOpen]);

    if (!isOpen && !isVisible) return null;

    // Fetch the correct dictionary for this strategy
    const stratData = STRATEGY_EXPLANATIONS[strategyKey] || DEFAULT_EXPLANATION;
    const content = stratData[language] || stratData["English"];

    const isHinglish = language === 'Hinglish';
    const isTelgish = language === 'Telgish';

    return (
        <div className={`guide-modal-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}>
            <div 
                className={`guide-modal-drawer glass-panel ${isOpen ? 'open' : ''}`} 
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="guide-header">
                    <div className="guide-title-row">
                        <BookOpen size={24} className="guide-icon" />
                        <h2 className="guide-title">{content.title || strategyName || 'Strategy Guide'}</h2>
                    </div>
                    <button className="guide-close-btn" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                {/* Body Content */}
                <div className="guide-body">
                    
                    {/* Premium Language Toggle */}
                    <div className="guide-lang-toggle-wrapper">
                        <div className="guide-lang-toggle">
                            <button 
                                className={`lang-btn ${language === 'English' ? 'active' : ''}`}
                                onClick={() => setLanguage('English')}
                            >English</button>
                            <button 
                                className={`lang-btn ${language === 'Hinglish' ? 'active' : ''}`}
                                onClick={() => setLanguage('Hinglish')}
                            >Hinglish</button>
                            <button 
                                className={`lang-btn ${language === 'Telgish' ? 'active' : ''}`}
                                onClick={() => setLanguage('Telgish')}
                            >Telgish</button>
                        </div>
                    </div>

                    <div className="guide-scroll-area">
                        {/* Concept Section */}
                        <div className="guide-section concept-section">
                            <h3 className="section-subtitle">
                                <Target size={16} /> 
                                {language === 'English' ? 'The Concept' : (isHinglish ? 'Concept Kya Hai?' : 'Concept Enti?')}
                            </h3>
                            <p className="guide-text">{content.concept}</p>
                        </div>

                        {/* The Math Section */}
                        <div className="guide-section math-section">
                           <div className="math-card">
                               <div className="math-card-header">
                                   <Calculator size={16} />
                                   <span>{language === 'English' ? 'The Math (Simplified)' : (isHinglish ? 'Maths Ka Formula' : 'Simplified Formula')}</span>
                               </div>
                               <div className="math-formula">
                                   {content.theMath}
                               </div>
                           </div>
                        </div>

                        {/* Real-world Example */}
                        <div className="guide-section example-section">
                            <h3 className="section-subtitle">
                                <Play size={16} /> 
                                {language === 'English' ? 'Real World Example' : (isHinglish ? 'Example (Udaharan)' : 'Real World Example')}
                            </h3>
                            <div className="example-box">
                                <p className="guide-text">{content.example}</p>
                            </div>
                        </div>

                        {/* Entry / Exit Rules */}
                        <div className="guide-rules-container">
                            <div className="rule-card entry-rule">
                                <div className="rule-card-header">
                                    <CheckCircle2 size={16} />
                                    <span>{language === 'English' ? 'Entry Rule' : (isHinglish ? 'Entry Kab Le?' : 'Eppudu Entry Teeskovali?')}</span>
                                </div>
                                <p className="rule-text">{content.entry}</p>
                            </div>

                            <div className="rule-card exit-rule">
                                <div className="rule-card-header">
                                    <LogOut size={16} />
                                    <span>{language === 'English' ? 'Exit Rule' : (isHinglish ? 'Exit Kab Karein?' : 'Eppudu Exit Avaali?')}</span>
                                </div>
                                <p className="rule-text">{content.exit}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
