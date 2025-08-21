#!/usr/bin/env python3
"""
Performance Metrics Correlation Analysis Tool

This program analyzes correlations between different performance metrics across
multiple benchmarks and configurations (hybrid, purecap, purecap-benchmark).
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import argparse
import os
from typing import Dict, List, Tuple, Optional

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class MetricCorrelationAnalyzer:
    def __init__(self, data_file: str = "raw-profiling-pmu-event-data.txt"):
        """Initialize the analyzer with performance data."""
        self.data_file = data_file
        self.configs = ['hybrid', 'purecap', 'purecap-benchmark']  # Define configs first
        self.data = self._load_data()
        self.df = self._create_dataframe()
        
    def _load_data(self) -> Dict:
        """Load performance data from file."""
        if not os.path.exists(self.data_file):
            print(f"Warning: {self.data_file} not found. Using sample data.")
            return self._get_sample_data()
        
        try:
            with open(self.data_file, 'r') as f:
                content = f.read()
                # Convert string representation to actual dict
                data = eval(content)
                return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return self._get_sample_data()
    
    def _get_sample_data(self) -> Dict:
        """Return sample data for testing."""
        return {
            'sample_benchmark': {
                'inst_retired': (1967936, 14482, 2847685),
                'cpu_cycles': (1220491, 7358, 2409026),
                'stall_backend': (345611, 2194, 960184),
                'stall_frontend': (114636, 296, 171753),
                'mem_access': (605878, 3692, 1016191),
                'cap_mem_access_rd': (12876, 474, 378906),
                'cap_mem_access_wr': (8329, 240, 230699),
            }
        }
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert raw data to pandas DataFrame for analysis."""
        rows = []
        
        for benchmark, metrics in self.data.items():
            for metric_name, values in metrics.items():
                for i, config in enumerate(self.configs):
                    rows.append({
                        'benchmark': benchmark,
                        'metric': metric_name,
                        'config': config,
                        'value': values[i] if i < len(values) else 0
                    })
        
        return pd.DataFrame(rows)
    
    def correlation_matrix(self, config: str = 'hybrid', 
                         metrics: Optional[List[str]] = None,
                         save_path: str = "correlation_matrix.png") -> None:
        """Create correlation matrix heatmap for specified configuration."""
        # Filter data for the specified configuration
        config_data = self.df[self.df['config'] == config].pivot(
            index='benchmark', columns='metric', values='value'
        )
        
        # Select specific metrics if provided
        if metrics:
            available_metrics = [m for m in metrics if m in config_data.columns]
            if not available_metrics:
                print(f"Warning: None of the specified metrics found in data")
                return
            config_data = config_data[available_metrics]
        
        # Calculate correlation matrix
        corr_matrix = config_data.corr()
        
        # Create heatmap
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        sns.heatmap(corr_matrix, 
                   mask=mask,
                   annot=False, 
                   cmap='coolwarm', 
                   cbar=False,
                   center=0,
                   square=True,
                   fmt='.2f',
                   cbar_kws={"shrink": .8})
        
        # plt.title(f'Performance Metrics Correlation Matrix ({config})')
        plt.ylabel('')  # Disable y label
        plt.xlabel('')  # Disable x label
        plt.yticks(fontsize=25)
        plt.xticks(fontsize=25)
        plt.tight_layout()
        plt.savefig(f'{save_path}-{config}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return corr_matrix
    
    def scatter_plot_matrix(self, config: str = 'hybrid',
                           metrics: Optional[List[str]] = None,
                           save_path: str = "scatter_matrix.png") -> None:
        """Create scatter plot matrix for key metrics."""
        # Filter data for the specified configuration
        config_data = self.df[self.df['config'] == config].pivot(
            index='benchmark', columns='metric', values='value'
        )
        
        # Select metrics (default to key ones if not specified)
        if not metrics:
            key_metrics = ['inst_retired', 'cpu_cycles', 'mem_access', 
                          'cap_mem_access_rd', 'cap_mem_access_wr']
            metrics = [m for m in key_metrics if m in config_data.columns]
        else:
            metrics = [m for m in metrics if m in config_data.columns]
        
        if len(metrics) < 2:
            print("Need at least 2 metrics for scatter matrix")
            return
        
        config_data = config_data[metrics]
        
        # Create scatter matrix
        fig = sns.pairplot(config_data, diag_kind='kde')
        fig.fig.suptitle(f'Scatter Plot Matrix - {config}', y=1.02)
        fig.fig.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def radar_chart(self, benchmark: str, save_path: str = "radar_chart.png") -> None:
        """Create radar chart comparing configurations for a specific benchmark."""
        # Get data for the benchmark
        bench_data = self.df[self.df['benchmark'] == benchmark]
        
        # Select key metrics for visualization
        key_metrics = ['inst_retired', 'cpu_cycles', 'mem_access', 
                      'cap_mem_access_rd', 'cap_mem_access_wr', 'stall_backend']
        available_metrics = [m for m in key_metrics if m in bench_data['metric'].values]
        
        if len(available_metrics) < 3:
            print("Need at least 3 metrics for radar chart")
            return
        
        # Prepare data for radar chart
        angles = np.linspace(0, 2 * np.pi, len(available_metrics), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = ['blue', 'red', 'green']
        
        for i, config in enumerate(self.configs):
            config_data = bench_data[bench_data['config'] == config]
            values = []
            
            for metric in available_metrics:
                metric_data = config_data[config_data['metric'] == metric]
                if not metric_data.empty:
                    values.append(metric_data['value'].iloc[0])
                else:
                    values.append(0)
            
            # Normalize values for better visualization
            values = np.array(values)
            if values.max() > 0:
                values = values / values.max()
            
            values = np.concatenate((values, [values[0]]))  # Complete the circle
            
            ax.plot(angles, values, 'o-', linewidth=2, label=config, color=colors[i])
            ax.fill(angles, values, alpha=0.25, color=colors[i])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(available_metrics)
        ax.set_ylim(0, 1)
        ax.set_title(f'Performance Profile: {benchmark}', size=16, y=1.08)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def pca_analysis(self, config: str = 'hybrid',
                    save_path: str = "pca_analysis.png") -> None:
        """Perform PCA analysis on performance metrics."""
        # Filter data for the specified configuration
        config_data = self.df[self.df['config'] == config].pivot(
            index='benchmark', columns='metric', values='value'
        )
        
        # Remove columns with zero variance
        config_data = config_data.loc[:, config_data.var() > 0]
        
        if config_data.shape[1] < 2:
            print("Need at least 2 metrics with variance for PCA")
            return
        
        # Standardize the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(config_data)
        
        # Perform PCA
        pca = PCA()
        pca_result = pca.fit_transform(scaled_data)
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Scatter plot of first two components
        ax1.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.7)
        for i, benchmark in enumerate(config_data.index):
            ax1.annotate(benchmark, (pca_result[i, 0], pca_result[i, 1]))
        
        ax1.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
        ax1.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
        ax1.set_title(f'PCA: First Two Components ({config})')
        ax1.grid(True, alpha=0.3)
        
        # Explained variance plot
        cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
        ax2.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, 'bo-')
        ax2.set_xlabel('Number of Components')
        ax2.set_ylabel('Cumulative Explained Variance Ratio')
        ax2.set_title('Explained Variance vs Number of Components')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0.95, color='r', linestyle='--', alpha=0.7, label='95% threshold')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        # Print component loadings
        print(f"\nPCA Component Loadings for {config}:")
        loadings_df = pd.DataFrame(
            pca.components_.T,
            columns=[f'PC{i+1}' for i in range(pca.components_.shape[0])],
            index=config_data.columns
        )
        print(loadings_df.head(10))
    
    def metric_comparison_bar(self, metrics: List[str], 
                            save_path: str = "metric_comparison.png") -> None:
        """Create bar chart comparing metrics across configurations."""
        # Filter data for specified metrics
        filtered_data = self.df[self.df['metric'].isin(metrics)]
        
        if filtered_data.empty:
            print("No data found for specified metrics")
            return
        
        # Create grouped bar chart
        plt.figure(figsize=(15, 8))
        
        # Pivot data for easier plotting
        pivot_data = filtered_data.pivot_table(
            index='metric', columns='config', values='value', aggfunc='mean'
        )
        
        # Create bar chart
        ax = pivot_data.plot(kind='bar', figsize=(15, 8))
        plt.title('Average Metric Values Across Configurations')
        plt.xlabel('Metrics')
        plt.ylabel('Average Value')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Configuration')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def combined_correlation_matrix(self, 
                                  metrics: Optional[List[str]] = None,
                                  save_path: str = "combined_correlation_matrix.png") -> np.ndarray:
        """Create combined correlation matrix heatmap with hybrid (left triangle) and purecap (right triangle)."""
        # Get data for both configurations
        hybrid_data = self.df[self.df['config'] == 'hybrid'].pivot(
            index='benchmark', columns='metric', values='value'
        )
        purecap_data = self.df[self.df['config'] == 'purecap'].pivot(
            index='benchmark', columns='metric', values='value'
        )
        
        # Select specific metrics if provided
        if metrics:
            available_metrics = [m for m in metrics if m in hybrid_data.columns and m in purecap_data.columns]
            if not available_metrics:
                print(f"Warning: None of the specified metrics found in data")
                return np.array([])
            hybrid_data = hybrid_data[available_metrics]
            purecap_data = purecap_data[available_metrics]
        
        # Calculate correlation matrices
        hybrid_corr = hybrid_data.corr()
        purecap_corr = purecap_data.corr()
        
        # Create combined matrix
        n_metrics = len(hybrid_corr)
        combined_matrix = np.zeros((n_metrics, n_metrics))
        
        # Fill left triangle (lower triangle) with hybrid correlations
        # Use proper indexing for lower triangle
        for i in range(n_metrics):
            for j in range(i + 1):  # Include diagonal (j <= i)
                combined_matrix[i, j] = hybrid_corr.iloc[i, j]
        
        # Fill right triangle (upper triangle) with purecap correlations
        # Use proper indexing for upper triangle
        for i in range(n_metrics):
            for j in range(i, n_metrics):  # Include diagonal (j >= i)
                combined_matrix[i, j] = purecap_corr.iloc[i, j]
        
        # Create heatmap
        plt.figure(figsize=(12, 10))
        
        plt.tick_params(
            axis='y',
            left=True, labelleft=True,
            right=True, labelright=True
        )

        # Create custom mask to show only the relevant triangles
        # We'll show the full matrix but annotate differently
        sns.heatmap(combined_matrix, 
                   annot=False, 
                   cmap='coolwarm', 
                   center=0,
                   square=True,
                   fmt='.2f',
                   cbar_kws={"shrink": .8,'aspect': 60, 'location': 'top', 'orientation': 'horizontal'},
                   xticklabels=hybrid_corr.columns,
                   yticklabels=hybrid_corr.columns)
        
        # Add text annotations to indicate which triangle is which
        plt.text(0.02, 0.98, 'Hybrid ABI(Lower Triangle)', 
                transform=plt.gca().transAxes, 
                fontsize=18, fontweight='bold',
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
        
        plt.text(0.98, 0.02, 'Purecap ABI (Upper Triangle)', 
                transform=plt.gca().transAxes, 
                fontsize=18, fontweight='bold',
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
        
        # plt.title('Combined Correlation Matrix: Hybrid vs Purecap', fontsize=14, fontweight='bold')
        plt.ylabel('')  # Disable y label
        plt.xlabel('')  # Disable x label
        plt.xticks(fontsize=13)
        plt.yticks(fontsize=13)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        return combined_matrix
    
    def interactive_dashboard(self):
        """Create an interactive dashboard for metric exploration."""
        print("Available chart types:")
        print("1. Correlation Matrix")
        print("2. Scatter Plot Matrix")
        print("3. Radar Chart")
        print("4. PCA Analysis")
        print("5. Metric Comparison Bar Chart")
        print("6. Combined Correlation Matrix (Hybrid vs Purecap)")
        print("7. All Charts")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            config = input("Enter configuration (hybrid/purecap/purecap-benchmark): ").strip()
            self.correlation_matrix(config=config)
            
        elif choice == "2":
            config = input("Enter configuration (hybrid/purecap/purecap-benchmark): ").strip()
            self.scatter_plot_matrix(config=config)
            
        elif choice == "3":
            benchmark = input("Enter benchmark name: ").strip()
            self.radar_chart(benchmark=benchmark)
            
        elif choice == "4":
            config = input("Enter configuration (hybrid/purecap/purecap-benchmark): ").strip()
            self.pca_analysis(config=config)
            
        elif choice == "5":
            metrics_input = input("Enter metrics (comma-separated): ").strip()
            metrics = [m.strip() for m in metrics_input.split(',')]
            self.metric_comparison_bar(metrics=metrics)
            
        elif choice == "6":
            metrics_input = input("Enter metrics (comma-separated, or press Enter for default): ").strip()
            if metrics_input:
                metrics = [m.strip() for m in metrics_input.split(',')]
            else:
                metrics = None
            self.combined_correlation_matrix(metrics=metrics)
            
        elif choice == "7":
            # Generate all charts
            for config in self.configs:
                self.correlation_matrix(config=config, 
                                     save_path=f"correlation_matrix_{config}.png")
                self.scatter_plot_matrix(config=config, 
                                       save_path=f"scatter_matrix_{config}.png")
                self.pca_analysis(config=config, 
                                save_path=f"pca_analysis_{config}.png")
            
            # Generate radar charts for first few benchmarks
            benchmarks = list(self.data.keys())[:3]
            for benchmark in benchmarks:
                self.radar_chart(benchmark=benchmark, 
                               save_path=f"radar_chart_{benchmark}.png")
            
            # Generate metric comparison
            key_metrics = ['inst_retired', 'cpu_cycles', 'mem_access', 
                          'cap_mem_access_rd', 'cap_mem_access_wr']
            self.metric_comparison_bar(metrics=key_metrics)
            
            # Generate combined correlation matrix
            self.combined_correlation_matrix(metrics=key_metrics,
                                             save_path=f"combined_correlation_matrix.png")
            
        else:
            print("Invalid choice!")

def main():
    parser = argparse.ArgumentParser(description='Performance Metrics Correlation Analysis')
    parser.add_argument('--data-file', default='raw-profiling-pmu-event-data.txt',
                       help='Path to the performance data file')
    parser.add_argument('--interactive', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--chart-type', choices=['correlation', 'scatter', 'radar', 'pca', 'bar', 'combined'],
                       help='Type of chart to generate')
    parser.add_argument('--config', choices=['hybrid', 'purecap', 'purecap-benchmark'],
                       default='hybrid', help='Configuration to analyze')
    parser.add_argument('--benchmark', help='Benchmark name for radar chart')
    parser.add_argument('--metrics', nargs='+', help='Metrics to analyze')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = MetricCorrelationAnalyzer(args.data_file)
    
    if args.interactive:
        analyzer.interactive_dashboard()
    else:
        if args.chart_type == 'correlation':
            analyzer.correlation_matrix(config=args.config, 
                                     metrics=args.metrics,
                                     save_path=args.output or 'metric-correlation_matrix.png')
        elif args.chart_type == 'scatter':
            analyzer.scatter_plot_matrix(config=args.config,
                                       metrics=args.metrics,
                                       save_path=args.output or 'metric-scatter_matrix.png')
        elif args.chart_type == 'radar':
            if not args.benchmark:
                print("Benchmark name required for radar chart")
                return
            analyzer.radar_chart(benchmark=args.benchmark,
                               save_path=args.output or 'metric-radar_chart.png')
        elif args.chart_type == 'pca':
            analyzer.pca_analysis(config=args.config,
                                save_path=args.output or 'metric-pca_analysis.png')
        elif args.chart_type == 'bar':
            if not args.metrics:
                print("Metrics required for bar chart")
                return
            analyzer.metric_comparison_bar(metrics=args.metrics,
                                         save_path=args.output or 'metric_comparison.png')
        elif args.chart_type == 'combined':
            analyzer.combined_correlation_matrix(metrics=args.metrics,
                                               save_path=args.output or 'figure7-metric-correlation.png')
        else:
            print("Please specify a chart type or use --interactive")

if __name__ == "__main__":
    main() 

    # python ./metric-correlation.py --chart-type  combined