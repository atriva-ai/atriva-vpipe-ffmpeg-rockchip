#!/usr/bin/env python3
"""
Results Analyzer for Video Pipeline Profiling Tests
Parses JSON results and generates visualizations
"""

import json
import argparse
import sys
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import os

class ResultsAnalyzer:
    """Analyze profiling test results"""
    
    def __init__(self, results_file: str):
        self.results_file = results_file
        self.data = None
        self.load_results()
        
    def load_results(self):
        """Load results from JSON file"""
        try:
            with open(self.results_file, 'r') as f:
                self.data = json.load(f)
            print(f"✅ Loaded results from {self.results_file}")
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            sys.exit(1)
            
    def get_summary(self) -> Dict:
        """Get test summary"""
        return self.data.get('summary', {})
        
    def get_metrics_df(self) -> pd.DataFrame:
        """Convert metrics to pandas DataFrame"""
        metrics = self.data.get('metrics', [])
        if not metrics:
            return pd.DataFrame()
            
        df = pd.DataFrame(metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
        
    def print_summary(self):
        """Print detailed summary"""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("📊 DETAILED TEST SUMMARY")
        print("="*80)
        print(f"📈 Total Metrics Collected: {summary.get('total_metrics', 0)}")
        print(f"🕐 Test Start: {summary.get('test_start', 'Unknown')}")
        print(f"🕐 Test End: {summary.get('test_end', 'Unknown')}")
        print(f"📺 Max Active Channels: {summary.get('max_channels', 0)}")
        print(f"🔥 Max CPU Usage: {summary.get('max_cpu_percent', 0):.1f}%")
        print(f"💾 Max Memory Usage: {summary.get('max_memory_mb', 0):.1f}MB")
        print(f"🖼️ Total Frames Decoded: {summary.get('total_frames', 0)}")
        print(f"❌ Total Errors: {summary.get('total_errors', 0)}")
        
        # Calculate averages
        df = self.get_metrics_df()
        if not df.empty:
            print(f"📊 Average CPU Usage: {df['cpu_percent'].mean():.1f}%")
            print(f"📊 Average Memory Usage: {df['memory_mb'].mean():.1f}MB")
            print(f"📊 Average Active Channels: {df['active_channels'].mean():.1f}")
            
        print("="*80)
        
    def plot_metrics(self, output_dir: str = "plots"):
        """Generate plots of metrics over time"""
        df = self.get_metrics_df()
        if df.empty:
            print("❌ No metrics data available for plotting")
            return
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the plotting style
        plt.style.use('default')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Video Pipeline Profiling Results - {os.path.basename(self.results_file)}', fontsize=16)
        
        # CPU Usage over time
        axes[0, 0].plot(df['timestamp'], df['cpu_percent'], 'b-', linewidth=2)
        axes[0, 0].set_title('CPU Usage Over Time')
        axes[0, 0].set_ylabel('CPU Usage (%)')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Memory Usage over time
        axes[0, 1].plot(df['timestamp'], df['memory_mb'], 'r-', linewidth=2)
        axes[0, 1].set_title('Memory Usage Over Time')
        axes[0, 1].set_ylabel('Memory Usage (MB)')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Active Channels over time
        axes[1, 0].plot(df['timestamp'], df['active_channels'], 'g-', linewidth=2)
        axes[1, 0].set_title('Active Channels Over Time')
        axes[1, 0].set_ylabel('Number of Active Channels')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Total Frames over time
        axes[1, 1].plot(df['timestamp'], df['total_frames'], 'm-', linewidth=2)
        axes[1, 1].set_title('Total Frames Decoded Over Time')
        axes[1, 1].set_ylabel('Total Frames')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save the plot
        plot_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(self.results_file))[0]}_metrics.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Metrics plot saved to {plot_file}")
        plt.close()
        
    def plot_correlation(self, output_dir: str = "plots"):
        """Plot correlation between different metrics"""
        df = self.get_metrics_df()
        if df.empty:
            print("❌ No metrics data available for correlation analysis")
            return
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create correlation matrix
        correlation_cols = ['cpu_percent', 'memory_mb', 'active_channels', 'total_frames']
        correlation_df = df[correlation_cols].corr()
        
        # Plot correlation heatmap
        plt.figure(figsize=(10, 8))
        plt.imshow(correlation_df, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        plt.colorbar(label='Correlation Coefficient')
        plt.xticks(range(len(correlation_cols)), correlation_cols, rotation=45)
        plt.yticks(range(len(correlation_cols)), correlation_cols)
        plt.title('Correlation Matrix of Metrics')
        
        # Add correlation values as text
        for i in range(len(correlation_cols)):
            for j in range(len(correlation_cols)):
                plt.text(j, i, f'{correlation_df.iloc[i, j]:.2f}', 
                        ha='center', va='center', fontsize=10)
        
        plt.tight_layout()
        
        # Save the plot
        plot_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(self.results_file))[0]}_correlation.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Correlation plot saved to {plot_file}")
        plt.close()
        
    def generate_report(self, output_file: str = None):
        """Generate a comprehensive HTML report"""
        df = self.get_metrics_df()
        summary = self.get_summary()
        
        if output_file is None:
            output_file = f"{os.path.splitext(self.results_file)[0]}_report.html"
            
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Video Pipeline Profiling Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .metrics {{ background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .error {{ background-color: #ffe6e6; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .plot {{ text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Video Pipeline Profiling Report</h1>
                <p><strong>Test File:</strong> {self.results_file}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Test Summary</h2>
                <table>
                    <tr><td>Total Metrics Collected</td><td>{summary.get('total_metrics', 0)}</td></tr>
                    <tr><td>Test Start</td><td>{summary.get('test_start', 'Unknown')}</td></tr>
                    <tr><td>Test End</td><td>{summary.get('test_end', 'Unknown')}</td></tr>
                    <tr><td>Max Active Channels</td><td>{summary.get('max_channels', 0)}</td></tr>
                    <tr><td>Max CPU Usage</td><td>{summary.get('max_cpu_percent', 0):.1f}%</td></tr>
                    <tr><td>Max Memory Usage</td><td>{summary.get('max_memory_mb', 0):.1f}MB</td></tr>
                    <tr><td>Total Frames Decoded</td><td>{summary.get('total_frames', 0)}</td></tr>
                    <tr><td>Total Errors</td><td>{summary.get('total_errors', 0)}</td></tr>
                </table>
            </div>
        """
        
        if not df.empty:
            html_content += f"""
            <div class="metrics">
                <h2>📈 Metrics Statistics</h2>
                <table>
                    <tr><th>Metric</th><th>Average</th><th>Min</th><th>Max</th><th>Std Dev</th></tr>
                    <tr><td>CPU Usage (%)</td><td>{df['cpu_percent'].mean():.1f}</td><td>{df['cpu_percent'].min():.1f}</td><td>{df['cpu_percent'].max():.1f}</td><td>{df['cpu_percent'].std():.1f}</td></tr>
                    <tr><td>Memory Usage (MB)</td><td>{df['memory_mb'].mean():.1f}</td><td>{df['memory_mb'].min():.1f}</td><td>{df['memory_mb'].max():.1f}</td><td>{df['memory_mb'].std():.1f}</td></tr>
                    <tr><td>Active Channels</td><td>{df['active_channels'].mean():.1f}</td><td>{df['active_channels'].min():.1f}</td><td>{df['active_channels'].max():.1f}</td><td>{df['active_channels'].std():.1f}</td></tr>
                    <tr><td>Total Frames</td><td>{df['total_frames'].mean():.1f}</td><td>{df['total_frames'].min():.1f}</td><td>{df['total_frames'].max():.1f}</td><td>{df['total_frames'].std():.1f}</td></tr>
                </table>
            </div>
            """
            
        errors = self.data.get('errors', [])
        if errors:
            html_content += f"""
            <div class="error">
                <h2>❌ Errors ({len(errors)})</h2>
                <ul>
            """
            for error in errors:
                html_content += f"<li>{error}</li>"
            html_content += "</ul></div>"
            
        html_content += """
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        print(f"📄 HTML report saved to {output_file}")

def compare_results(result_files: List[str], output_dir: str = "comparison"):
    """Compare multiple test results"""
    if len(result_files) < 2:
        print("❌ Need at least 2 result files for comparison")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Load all results
    results = []
    for file in result_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                results.append({
                    'file': file,
                    'name': os.path.splitext(os.path.basename(file))[0],
                    'data': data
                })
        except Exception as e:
            print(f"❌ Error loading {file}: {e}")
            continue
            
    if len(results) < 2:
        print("❌ Not enough valid result files for comparison")
        return
        
    # Create comparison plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Comparison of Video Pipeline Profiling Results', fontsize=16)
    
    # Compare max CPU usage
    names = [r['name'] for r in results]
    max_cpu = [r['data']['summary']['max_cpu_percent'] for r in results]
    axes[0, 0].bar(names, max_cpu, color='red', alpha=0.7)
    axes[0, 0].set_title('Max CPU Usage Comparison')
    axes[0, 0].set_ylabel('CPU Usage (%)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Compare max memory usage
    max_memory = [r['data']['summary']['max_memory_mb'] for r in results]
    axes[0, 1].bar(names, max_memory, color='blue', alpha=0.7)
    axes[0, 1].set_title('Max Memory Usage Comparison')
    axes[0, 1].set_ylabel('Memory Usage (MB)')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Compare max channels
    max_channels = [r['data']['summary']['max_channels'] for r in results]
    axes[1, 0].bar(names, max_channels, color='green', alpha=0.7)
    axes[1, 0].set_title('Max Active Channels Comparison')
    axes[1, 0].set_ylabel('Number of Channels')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Compare total frames
    total_frames = [r['data']['summary']['total_frames'] for r in results]
    axes[1, 1].bar(names, total_frames, color='purple', alpha=0.7)
    axes[1, 1].set_title('Total Frames Decoded Comparison')
    axes[1, 1].set_ylabel('Total Frames')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save comparison plot
    comparison_file = os.path.join(output_dir, "comparison_plot.png")
    plt.savefig(comparison_file, dpi=300, bbox_inches='tight')
    print(f"📊 Comparison plot saved to {comparison_file}")
    plt.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze Video Pipeline Profiling Results")
    parser.add_argument("results_file", help="JSON results file to analyze")
    parser.add_argument("--output-dir", default="plots", help="Output directory for plots")
    parser.add_argument("--compare", nargs="+", help="Compare multiple result files")
    parser.add_argument("--no-plots", action="store_true", help="Skip generating plots")
    parser.add_argument("--no-report", action="store_true", help="Skip generating HTML report")
    
    args = parser.parse_args()
    
    if args.compare:
        # Compare multiple results
        compare_results(args.compare, args.output_dir)
    else:
        # Analyze single result
        analyzer = ResultsAnalyzer(args.results_file)
        
        # Print summary
        analyzer.print_summary()
        
        # Generate plots
        if not args.no_plots:
            analyzer.plot_metrics(args.output_dir)
            analyzer.plot_correlation(args.output_dir)
            
        # Generate HTML report
        if not args.no_report:
            analyzer.generate_report()

if __name__ == "__main__":
    main()
