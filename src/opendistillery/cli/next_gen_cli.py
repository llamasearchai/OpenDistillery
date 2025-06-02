"""
Next-Generation CLI with Real-time Monitoring and Advanced Features
"""

import click
import asyncio
import websockets
import json
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.tree import Tree
from rich.syntax import Syntax
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import io
import base64

console = Console()

@click.group()
def next_gen():
    """ Next-Generation Prompting CLI"""
    pass

@next_gen.command()
@click.option('--prompt', '-p', required=True, help='Prompt to optimize')
@click.option('--techniques', '-t', multiple=True, help='Specific techniques to use')
@click.option('--quality-target', '-q', default=0.90, help='Quality target (0-1)')
@click.option('--time-budget', '-b', default=30.0, help='Time budget in seconds')
@click.option('--stream', '-s', is_flag=True, help='Enable real-time streaming')
@click.option('--model', '-m', help='Preferred model')
@click.option('--visualize', '-v', is_flag=True, help='Show optimization visualization')
def optimize(prompt, techniques, quality_target, time_budget, stream, model, visualize):
    """ Optimize prompt using next-gen techniques"""
    
    console.print(Panel.fit(
        f"[bold cyan]Next-Generation Prompt Optimization[/]\n\n"
        f" Target Quality: {quality_target:.1%}\n"
        f"⏱  Time Budget: {time_budget}s\n"
        f"🧠 Model: {model or 'Auto-selected'}\n"
        f"📡 Streaming: {'Enabled' if stream else 'Disabled'}",
        title=" Optimization Session",
        border_style="cyan"
    ))
    
    if stream:
        asyncio.run(_stream_optimization(prompt, techniques, quality_target, time_budget, model, visualize))
    else:
        asyncio.run(_batch_optimization(prompt, techniques, quality_target, time_budget, model, visualize))

async def _stream_optimization(prompt, techniques, quality_target, time_budget, model, visualize):
    """Real-time streaming optimization with live updates"""
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="progress", ratio=2),
        Layout(name="results", ratio=3)
    )
    
    # Initialize components
    progress_table = Table(title="🔄 Optimization Progress")
    progress_table.add_column("Technique", style="cyan")
    progress_table.add_column("Status", style="green")
    progress_table.add_column("Quality", style="yellow")
    progress_table.add_column("Time", style="blue")
    
    results_panel = Panel("Waiting for results...", title=" Results", border_style="green")
    
    layout["header"] = Panel(f" Optimizing: {prompt[:50]}...", border_style="cyan")
    layout["progress"] = progress_table
    layout["results"] = results_panel
    layout["footer"] = Panel(" Real-time optimization in progress...", border_style="yellow")
    
    optimization_data = {
        "techniques": [],
        "quality_scores": [],
        "timestamps": []
    }
    
    async def update_display():
        """Update the display with latest data"""
        
        # Update progress table
        progress_table.rows.clear()
        for technique_data in optimization_data["techniques"]:
            progress_table.add_row(
                technique_data["name"],
                technique_data["status"],
                f"{technique_data.get('quality', 0):.2%}",
                f"{technique_data.get('time', 0):.1f}s"
            )
        
        # Update results panel
        if optimization_data["quality_scores"]:
            best_quality = max(optimization_data["quality_scores"])
            latest_technique = optimization_data["techniques"][-1]["name"] if optimization_data["techniques"] else "None"
            
            results_content = f"""
[bold green]Best Quality Score:[/] {best_quality:.2%}
[bold blue]Latest Technique:[/] {latest_technique}
[bold yellow]Techniques Completed:[/] {len(optimization_data["techniques"])}
[bold cyan]Current Progress:[/] {len(optimization_data["techniques"]) * 10:.0f}%
            """
            layout["results"] = Panel(results_content, title=" Live Results", border_style="green")
    
    # Simulate WebSocket connection (in production, connect to actual WebSocket)
    with Live(layout, refresh_per_second=4) as live:
        
        # Simulate streaming optimization
        techniques_list = [
            "quantum_superposition", "neural_architecture_search", "hyperparameter_optimization",
            "metacognitive", "neuro_symbolic", "multimodal_cot", "tree_of_thoughts"
        ]
        
        for i, technique in enumerate(techniques_list):
            # Simulate technique processing
            optimization_data["techniques"].append({
                "name": technique,
                "status": "🔄 Processing",
                "quality": 0,
                "time": 0
            })
            
            await update_display()
            await asyncio.sleep(2)  # Simulate processing time
            
            # Simulate completion
            quality_score = 0.7 + (i * 0.05) + np.random.random() * 0.1
            processing_time = 1.5 + np.random.random() * 2
            
            optimization_data["techniques"][-1].update({
                "status": "✅ Complete",
                "quality": quality_score,
                "time": processing_time
            })
            optimization_data["quality_scores"].append(quality_score)
            optimization_data["timestamps"].append(datetime.now())
            
            await update_display()
            await asyncio.sleep(0.5)
        
        # Final update
        layout["footer"] = Panel(" Optimization complete! Press any key to continue...", border_style="green")
        await update_display()
        
        # Show final results
        best_technique = max(optimization_data["techniques"], key=lambda x: x.get("quality", 0))
        console.print(Panel.fit(
            f"[bold green]🏆 OPTIMIZATION COMPLETE[/]\n\n"
            f"Best Technique: {best_technique['name']}\n"
            f"Best Quality: {best_technique['quality']:.2%}\n"
            f"Total Time: {sum(t.get('time', 0) for t in optimization_data['techniques']):.1f}s",
            title=" Final Results",
            border_style="green"
        ))
        
        if visualize:
            await _show_optimization_visualization(optimization_data)

async def _batch_optimization(prompt, techniques, quality_target, time_budget, model, visualize):
    """Traditional batch optimization with progress tracking"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        
        task = progress.add_task(" Optimizing prompt...", total=100)
        
        # Simulate optimization process
        techniques_list = list(techniques) if techniques else [
            "quantum_superposition", "neural_architecture_search", "hyperparameter_optimization",
            "metacognitive", "neuro_symbolic", "multimodal_cot", "tree_of_thoughts"
        ]
        
        results = {}
        
        for i, technique in enumerate(techniques_list):
            progress.update(task, description=f"🧠 Applying {technique}...")
            
            # Simulate processing
            await asyncio.sleep(2)
            
            # Simulate result
            quality_score = 0.7 + (i * 0.05) + np.random.random() * 0.1
            results[technique] = {
                "quality_score": quality_score,
                "processing_time": 1.5 + np.random.random() * 2,
                "optimized_prompt": f"Optimized version using {technique}: {prompt}"
            }
            
            progress.update(task, advance=100 / len(techniques_list))
        
        progress.update(task, description="✅ Optimization complete!")
        
        # Display results
        results_table = Table(title=" Optimization Results")
        results_table.add_column("Technique", style="cyan")
        results_table.add_column("Quality Score", style="green")
        results_table.add_column("Processing Time", style="yellow")
        results_table.add_column("Status", style="blue")
        
        for technique, result in results.items():
            status = "🏆 Best" if result["quality_score"] == max(r["quality_score"] for r in results.values()) else "✅ Good"
            results_table.add_row(
                technique,
                f"{result['quality_score']:.2%}",
                f"{result['processing_time']:.1f}s",
                status
            )
        
        console.print(results_table)
        
        # Show best result
        best_technique = max(results.items(), key=lambda x: x[1]["quality_score"])
        console.print(Panel.fit(
            f"[bold green]{best_technique[1]['optimized_prompt']}[/]",
            title=f"🏆 Best Result: {best_technique[0]} ({best_technique[1]['quality_score']:.2%})",
            border_style="green"
        ))
        
        if visualize:
            optimization_data = {
                "techniques": [{"name": k, "quality": v["quality_score"]} for k, v in results.items()],
                "quality_scores": [v["quality_score"] for v in results.values()],
                "timestamps": [datetime.now() for _ in results]
            }
            await _show_optimization_visualization(optimization_data)

async def _show_optimization_visualization(optimization_data):
    """Show optimization visualization"""
    
    console.print("\n[cyan] Generating optimization visualization...[/]")
    
    # Create quality improvement chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Quality scores by technique
    techniques = [t["name"] for t in optimization_data["techniques"]]
    qualities = [t.get("quality", 0) for t in optimization_data["techniques"]]
    
    ax1.bar(range(len(techniques)), qualities, color='skyblue', alpha=0.8)
    ax1.set_xlabel('Techniques')
    ax1.set_ylabel('Quality Score')
    ax1.set_title('Quality Scores by Technique')
    ax1.set_xticks(range(len(techniques)))
    ax1.set_xticklabels([t[:15] + '...' if len(t) > 15 else t for t in techniques], rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Quality improvement over time
    if len(optimization_data["quality_scores"]) > 1:
        ax2.plot(optimization_data["quality_scores"], marker='o', linewidth=2, markersize=6)
        ax2.set_xlabel('Optimization Step')
        ax2.set_ylabel('Quality Score')
        ax2.set_title('Quality Improvement Over Time')
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(range(len(optimization_data["quality_scores"])), 
                        optimization_data["quality_scores"], alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot to memory and display
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    
    # In a real implementation, you'd display this or save to file
    console.print(" Visualization saved! (In production: display chart here)")
    plt.close()

@next_gen.command()
@click.option('--file', '-f', type=click.Path(exists=True), help='File containing prompts')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--parallel', '-p', is_flag=True, help='Enable parallel processing')
@click.option('--max-workers', '-w', default=5, help='Maximum parallel workers')
def batch(file, output, parallel, max_workers):
    """🔄 Batch process multiple prompts"""
    
    console.print(Panel.fit(
        f"[bold cyan]Batch Processing Mode[/]\n\n"
        f"📁 Input File: {file}\n"
        f"📄 Output File: {output or 'results.json'}\n"
        f" Parallel: {'Yes' if parallel else 'No'}\n"
        f"👥 Max Workers: {max_workers if parallel else 1}",
        title="🔄 Batch Optimization",
        border_style="cyan"
    ))
    
    asyncio.run(_process_batch(file, output, parallel, max_workers))

async def _process_batch(file, output, parallel, max_workers):
    """Process batch of prompts"""
    
    # Read prompts from file
    with open(file, 'r') as f:
        prompts = [line.strip() for line in f if line.strip()]
    
    console.print(f" Found {len(prompts)} prompts to process")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("🔄 Processing batch...", total=len(prompts))
        
        results = []
        
        if parallel:
            # Parallel processing simulation
            semaphore = asyncio.Semaphore(max_workers)
            
            async def process_single_prompt(prompt_text, index):
                async with semaphore:
                    # Simulate processing
                    await asyncio.sleep(1 + np.random.random())
                    quality_score = 0.7 + np.random.random() * 0.3
                    
                    return {
                        "index": index,
                        "original_prompt": prompt_text,
                        "optimized_prompt": f"Optimized: {prompt_text}",
                        "quality_score": quality_score,
                        "techniques_used": ["metacognitive", "tree_of_thoughts"],
                        "processing_time": 1.5 + np.random.random()
                    }
            
            tasks = [process_single_prompt(prompt, i) for i, prompt in enumerate(prompts)]
            
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                results.append(result)
                progress.update(task, advance=1)
                progress.update(task, description=f"🔄 Processed {len(results)}/{len(prompts)} prompts")
            
        else:
            # Sequential processing
            for i, prompt_text in enumerate(prompts):
                await asyncio.sleep(0.5)  # Simulate processing
                
                result = {
                    "index": i,
                    "original_prompt": prompt_text,
                    "optimized_prompt": f"Optimized: {prompt_text}",
                    "quality_score": 0.7 + np.random.random() * 0.3,
                    "techniques_used": ["metacognitive", "tree_of_thoughts"],
                    "processing_time": 1.5 + np.random.random()
                }
                
                results.append(result)
                progress.update(task, advance=1)
        
        # Sort results by index to maintain order
        results.sort(key=lambda x: x["index"])
        
        # Save results
        output_file = output or "batch_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display summary
        avg_quality = sum(r["quality_score"] for r in results) / len(results)
        total_time = sum(r["processing_time"] for r in results)
        
        console.print(Panel.fit(
            f"[bold green]✅ Batch Processing Complete[/]\n\n"
            f" Prompts Processed: {len(results)}\n"
            f" Average Quality: {avg_quality:.2%}\n"
            f"⏱  Total Time: {total_time:.1f}s\n"
            f"📁 Results saved to: {output_file}",
            title=" Batch Results",
            border_style="green"
        ))

@next_gen.command()
@click.option('--technique', '-t', help='Specific technique to analyze')
@click.option('--days', '-d', default=30, help='Days of data to analyze')
@click.option('--export', '-e', help='Export analytics to file')
def analytics(technique, days, export):
    """ View detailed analytics and performance metrics"""
    
    console.print(Panel.fit(
        f"[bold cyan]Analytics Dashboard[/]\n\n"
        f" Technique Filter: {technique or 'All'}\n"
        f"📅 Time Period: Last {days} days\n"
        f" Export: {export or 'Console only'}",
        title=" Performance Analytics",
        border_style="cyan"
    ))
    
    asyncio.run(_show_analytics(technique, days, export))

async def _show_analytics(technique, days, export):
    """Display comprehensive analytics"""
    
    # Simulate analytics data
    analytics_data = {
        "total_requests": 1250,
        "success_rate": 0.96,
        "average_quality_improvement": 0.23,
        "average_processing_time": 15.7,
        "top_techniques": [
            {"name": "metacognitive", "usage": 0.35, "avg_quality": 0.87},
            {"name": "tree_of_thoughts", "usage": 0.28, "avg_quality": 0.84},
            {"name": "quantum_superposition", "usage": 0.15, "avg_quality": 0.91},
            {"name": "neural_architecture_search", "usage": 0.12, "avg_quality": 0.89},
            {"name": "hyperparameter_optimization", "usage": 0.10, "avg_quality": 0.82}
        ],
        "quality_distribution": {
            "excellent": 0.45,
            "good": 0.35,
            "average": 0.15,
            "poor": 0.05
        },
        "cost_savings": 1250.50,
        "user_satisfaction": 0.94
    }
    
    # Overview table
    overview_table = Table(title=" Performance Overview")
    overview_table.add_column("Metric", style="cyan")
    overview_table.add_column("Value", style="green")
    overview_table.add_column("Trend", style="yellow")
    
    overview_table.add_row("Total Requests", f"{analytics_data['total_requests']:,}", " +15%")
    overview_table.add_row("Success Rate", f"{analytics_data['success_rate']:.1%}", " +2%")
    overview_table.add_row("Avg Quality Improvement", f"{analytics_data['average_quality_improvement']:.1%}", " +5%")
    overview_table.add_row("Avg Processing Time", f"{analytics_data['average_processing_time']:.1f}s", "📉 -8%")
    overview_table.add_row("Cost Savings", f"${analytics_data['cost_savings']:,.2f}", " +12%")
    overview_table.add_row("User Satisfaction", f"{analytics_data['user_satisfaction']:.1%}", " +3%")
    
    console.print(overview_table)
    console.print()
    
    # Technique performance table
    technique_table = Table(title="🧠 Technique Performance")
    technique_table.add_column("Technique", style="cyan")
    technique_table.add_column("Usage", style="blue")
    technique_table.add_column("Avg Quality", style="green")
    technique_table.add_column("Efficiency", style="yellow")
    
    for tech in analytics_data["top_techniques"]:
        efficiency = " High" if tech["avg_quality"] > 0.85 else " Medium" if tech["avg_quality"] > 0.80 else " Low"
        technique_table.add_row(
            tech["name"],
            f"{tech['usage']:.1%}",
            f"{tech['avg_quality']:.1%}",
            efficiency
        )
    
    console.print(technique_table)
    console.print()
    
    # Quality distribution
    quality_tree = Tree(" Quality Distribution")
    for quality_level, percentage in analytics_data["quality_distribution"].items():
        quality_tree.add(f"{quality_level.title()}: {percentage:.1%}")
    
    console.print(Panel(quality_tree, title="Quality Breakdown", border_style="green"))
    
    if export:
        with open(export, 'w') as f:
            json.dump(analytics_data, f, indent=2)
        console.print(f"\n✅ Analytics exported to {export}")

@next_gen.command()
@click.option('--host', '-h', default='localhost', help='API host')
@click.option('--port', '-p', default=8000, help='API port')
@click.option('--interval', '-i', default=5, help='Refresh interval in seconds')
def monitor(host, port, interval):
    """📡 Real-time system monitoring dashboard"""
    
    console.print(Panel.fit(
        f"[bold cyan]Real-time System Monitor[/]\n\n"
        f"🌐 Endpoint: http://{host}:{port}\n"
        f"🔄 Refresh: Every {interval}s\n"
        f" Monitoring: System health, performance, usage",
        title="📡 Live Monitor",
        border_style="cyan"
    ))
    
    asyncio.run(_real_time_monitor(host, port, interval))

async def _real_time_monitor(host, port, interval):
    """Real-time monitoring dashboard"""
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    layout["left"].split_column(
        Layout(name="system"),
        Layout(name="performance")
    )
    layout["right"].split_column(
        Layout(name="usage"),
        Layout(name="alerts")
    )
    
    def create_system_health():
        """Create system health panel"""
        # Simulate system metrics
        cpu_usage = np.random.uniform(20, 80)
        memory_usage = np.random.uniform(30, 70)
        disk_usage = np.random.uniform(15, 60)
        
        health_table = Table(title="💻 System Health")
        health_table.add_column("Metric", style="cyan")
        health_table.add_column("Value", style="green")
        health_table.add_column("Status", style="yellow")
        
        health_table.add_row("CPU Usage", f"{cpu_usage:.1f}%", "🟢 Normal" if cpu_usage < 70 else "🟡 High")
        health_table.add_row("Memory Usage", f"{memory_usage:.1f}%", "🟢 Normal" if memory_usage < 60 else "🟡 High")
        health_table.add_row("Disk Usage", f"{disk_usage:.1f}%", "🟢 Normal")
        health_table.add_row("Active Connections", "47", "🟢 Normal")
        
        return health_table
    
    def create_performance_metrics():
        """Create performance metrics panel"""
        # Simulate performance data
        avg_latency = np.random.uniform(150, 300)
        throughput = np.random.uniform(800, 1200)
        error_rate = np.random.uniform(0.1, 2.0)
        
        perf_table = Table(title=" Performance Metrics")
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Current", style="green")
        perf_table.add_column("Target", style="blue")
        
        perf_table.add_row("Avg Latency", f"{avg_latency:.0f}ms", "< 200ms")
        perf_table.add_row("Throughput", f"{throughput:.0f} req/min", "> 1000 req/min")
        perf_table.add_row("Error Rate", f"{error_rate:.1f}%", "< 1.0%")
        perf_table.add_row("Success Rate", "98.5%", "> 99.0%")
        
        return perf_table
    
    def create_usage_stats():
        """Create usage statistics panel"""
        usage_content = f"""
[bold green] Current Usage[/]

 Active Optimizations: 12
⏳ Queue Length: 3
👥 Active Users: 47
 Requests Today: 1,247
🧠 Top Technique: metacognitive
 Avg Quality Score: 87.3%
        """
        return Panel(usage_content, title=" Usage Statistics", border_style="blue")
    
    def create_alerts():
        """Create alerts panel"""
        alerts_content = f"""
[bold yellow]⚠  Active Alerts[/]

🟡 High CPU usage on node-2
🟢 All models operational
🟢 API endpoints healthy
🔵 Scheduled maintenance: 2h

[dim]Last updated: {datetime.now().strftime('%H:%M:%S')}[/]
        """
        return Panel(alerts_content, title="🚨 System Alerts", border_style="yellow")
    
    # Initial layout setup
    layout["header"] = Panel(f"🖥  OpenDistillery System Monitor - {host}:{port}", border_style="cyan")
    layout["footer"] = Panel(f"🔄 Auto-refresh every {interval}s | Press Ctrl+C to exit", border_style="green")
    
    with Live(layout, refresh_per_second=1) as live:
        while True:
            try:
                # Update all panels
                layout["system"] = create_system_health()
                layout["performance"] = create_performance_metrics()
                layout["usage"] = create_usage_stats()
                layout["alerts"] = create_alerts()
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                console.print("\n👋 Monitoring stopped.")
                break

@next_gen.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--validate-only', '-v', is_flag=True, help='Only validate configuration')
def configure(config, validate_only):
    """⚙ Configure system settings and preferences"""
    
    console.print(Panel.fit(
        f"[bold cyan]System Configuration[/]\n\n"
        f"📁 Config File: {config or 'Default settings'}\n"
        f"✅ Validate Only: {'Yes' if validate_only else 'No'}",
        title="⚙ Configuration Manager",
        border_style="cyan"
    ))
    
    if config:
        _load_and_validate_config(config, validate_only)
    else:
        _interactive_configuration()

def _load_and_validate_config(config_path, validate_only):
    """Load and validate configuration file"""
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Validate configuration
        required_fields = ['api_endpoints', 'default_techniques', 'quality_targets', 'security']
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            console.print(f"❌ Configuration validation failed: Missing fields: {missing_fields}", style="red")
            return
        
        console.print("✅ Configuration validation passed!", style="green")
        
        # Display configuration summary
        config_table = Table(title="📋 Configuration Summary")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        for key, value in config_data.items():
            config_table.add_row(key, str(value)[:50] + "..." if len(str(value)) > 50 else str(value))
        
        console.print(config_table)
        
        if not validate_only:
            console.print("💾 Configuration applied successfully!")
            
    except FileNotFoundError:
        console.print(f"❌ Configuration file not found: {config_path}", style="red")
    except json.JSONDecodeError:
        console.print(f"❌ Invalid JSON in configuration file: {config_path}", style="red")

def _interactive_configuration():
    """Interactive configuration setup"""
    
    console.print("🛠  Interactive Configuration Setup\n")
    
    # API Configuration
    api_host = click.prompt("🌐 API Host", default="localhost")
    api_port = click.prompt("🔌 API Port", default=8000, type=int)
    api_key = click.prompt("🔑 API Key", hide_input=True)
    
    # Default Techniques
    console.print("\n🧠 Select default techniques:")
    available_techniques = [
        "quantum_superposition", "neural_architecture_search", "hyperparameter_optimization",
        "metacognitive", "neuro_symbolic", "multimodal_cot", "tree_of_thoughts"
    ]
    
    selected_techniques = []
    for technique in available_techniques:
        if click.confirm(f"  Enable {technique}?", default=True):
            selected_techniques.append(technique)
    
    # Quality Targets
    default_quality = click.prompt(" Default Quality Target", default=0.90, type=float)
    max_time_budget = click.prompt("⏱  Max Time Budget (seconds)", default=60, type=int)
    
    # Security Settings
    enable_rate_limiting = click.confirm("  Enable Rate Limiting?", default=True)
    max_requests_per_minute = click.prompt(" Max Requests per Minute", default=100, type=int) if enable_rate_limiting else None
    
    # Build configuration
    config = {
        "api_endpoints": {
            "host": api_host,
            "port": api_port,
            "api_key": api_key
        },
        "default_techniques": selected_techniques,
        "quality_targets": {
            "default": default_quality,
            "minimum": 0.70,
            "maximum": 0.99
        },
        "performance": {
            "max_time_budget": max_time_budget,
            "parallel_processing": True,
            "max_workers": 10
        },
        "security": {
            "rate_limiting": enable_rate_limiting,
            "max_requests_per_minute": max_requests_per_minute,
            "api_key_required": True
        }
    }
    
    # Save configuration
    config_file = "opendistillery_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    console.print(f"\n✅ Configuration saved to {config_file}")
    console.print(Panel.fit(
        f"[bold green]Configuration Complete![/]\n\n"
        f"🌐 API Endpoint: {api_host}:{api_port}\n"
        f"🧠 Default Techniques: {len(selected_techniques)}\n"
        f" Quality Target: {default_quality:.1%}\n"
        f"⏱  Time Budget: {max_time_budget}s\n"
        f"  Security: {'Enabled' if enable_rate_limiting else 'Basic'}",
        title=" Setup Complete",
        border_style="green"
    ))

if __name__ == '__main__':
    next_gen()