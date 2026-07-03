import React, { useState, useEffect } from 'react';
import { X, Info, Calculator, Play, Target, Lightbulb, Sparkles } from 'lucide-react';
import { METRIC_EXPLANATIONS, DEFAULT_METRIC } from '../data/metricExplanations';
import '../index.css';

export default function MetricGuideModal({ isOpen, onClose, metricKey, metricName }) {
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

    // Fetch the correct dictionary for this metric
    const metricData = METRIC_EXPLANATIONS[metricKey] || DEFAULT_METRIC;
    const content = metricData[language] || metricData["English"];

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
                        <Info size={24} className="guide-icon" style={{ color: 'var(--accent-cyan)' }} />
                        <h2 className="guide-title">{content.title || metricName || 'Metric Guide'}</h2>
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
                                {language === 'English' ? 'What is this?' : (isHinglish ? 'Yeh Kya Hai?' : 'Idhi Enti?')}
                            </h3>
                            <p className="guide-text">{content.concept}</p>
                        </div>

                        {/* The Math Section */}
                        <div className="guide-section math-section">
                           <div className="math-card" style={{ borderColor: 'rgba(56, 189, 248, 0.2)', background: 'rgba(56, 189, 248, 0.04)' }}>
                               <div className="math-card-header" style={{ color: 'var(--accent-cyan)', background: 'rgba(56, 189, 248, 0.1)', borderBottomColor: 'rgba(56, 189, 248, 0.1)' }}>
                                   <Calculator size={16} />
                                   <span>{language === 'English' ? 'The Math' : (isHinglish ? 'Maths Ka Formula' : 'Simplified Formula')}</span>
                               </div>
                               <div className="math-formula">
                                   {content.theMath}
                               </div>
                           </div>
                        </div>

                        {/* Example */}
                        <div className="guide-section example-section">
                            <h3 className="section-subtitle">
                                <Play size={16} /> 
                                {language === 'English' ? 'Real World Example' : (isHinglish ? 'Example (Udaharan)' : 'Real World Example')}
                            </h3>
                            <div className="example-box">
                                <p className="guide-text">{content.example}</p>
                            </div>
                        </div>

                        {/* Why It Matters - UPGRADED TO ULTRA PREMIUM */}
                        <div className="guide-section" style={{ marginTop: '24px' }}>
                            <div className="premium-insight-card">
                                <div className="premium-insight-header">
                                    <div className="premium-insight-icon-wrap">
                                        <Lightbulb size={18} className="insight-icon-svg" />
                                    </div>
                                    <h3 className="premium-insight-title">
                                        {language === 'English' ? 'Why It Matters' : (isHinglish ? 'Yeh Kyun Zaroori Hai?' : 'Idi Enduku Mukhyam?')}
                                    </h3>
                                    <Sparkles size={14} className="insight-sparkle" />
                                </div>
                                <div className="premium-insight-body">
                                    <p className="insight-text">{content.whyItMatters}</p>
                                </div>
                            </div>
                        </div>
                        
                    </div>
                </div>
            </div>
        </div>
    );
}
