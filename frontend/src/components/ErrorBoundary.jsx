import { Component } from 'react';

export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        console.error('ErrorBoundary caught:', error, info);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    padding: 24,
                    background: 'rgba(239,68,68,0.06)',
                    border: '1px solid rgba(239,68,68,0.2)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--color-loss)',
                    fontSize: '0.85rem',
                }}>
                    <strong>Something went wrong rendering this section.</strong>
                    <pre style={{ marginTop: 8, fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'pre-wrap' }}>
                        {this.state.error?.message}
                    </pre>
                    <button
                        onClick={() => this.setState({ hasError: false, error: null })}
                        style={{
                            marginTop: 12, padding: '6px 14px', background: 'var(--bg-elevated)',
                            border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)',
                            color: 'var(--text-primary)', cursor: 'pointer', fontSize: '0.8rem',
                        }}
                    >
                        Retry
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
