/**
 * MIB Viewer - Tree Visualization JavaScript
 */

class TreeVisualization {
    constructor(containerId, data) {
        this.containerId = containerId;
        this.data = data;
        this.svg = null;
        this.g = null;
        this.tree = null;
        this.root = null;
        this.currentRoot = data;
        this.width = 0;
        this.height = 0;
        this.margin = { top: 20, right: 120, bottom: 20, left: 120 };
        this.duration = 750;
        this.i = 0;
        this.searchResults = [];
        this.currentLayout = 'tree'; // 'tree' or 'radial'

        this.initialize();
    }

    initialize() {
        this.setupDimensions();
        this.setupSVG();
        this.setupTree();
        this.setupZoom();
        this.render();
    }

    setupDimensions() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            throw new Error(`Container with id '${this.containerId}' not found`);
        }

        this.width = container.clientWidth;
        this.height = container.clientHeight;
    }

    setupSVG() {
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);

        this.g = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);
    }

    setupTree() {
        const treeWidth = this.width - this.margin.right - this.margin.left;
        const treeHeight = this.height - this.margin.top - this.margin.bottom;

        this.tree = d3.tree()
            .size([treeHeight, treeWidth]);

        // Convert data to hierarchy
        this.root = d3.hierarchy(this.currentRoot, d => d.children);
        this.root.x0 = treeHeight / 2;
        this.root.y0 = 0;

        // Collapse all children initially except first level
        if (this.root.children) {
            this.root.children.forEach(this.collapse.bind(this));
        }
    }

    setupZoom() {
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(zoom);
    }

    collapse(d) {
        if (d.children) {
            d._children = d.children;
            d._children.forEach(this.collapse.bind(this));
            d.children = null;
        }
    }

    expand(d) {
        if (d._children) {
            d.children = d._children;
            d.children.forEach(this.expand.bind(this));
            d._children = null;
        }
    }

    render() {
        this.update(this.root);
    }

    update(source) {
        // Calculate new tree layout
        const treeData = this.tree(this.root);
        const nodes = treeData.descendants();
        const links = treeData.links();

        // Normalize for fixed-depth
        nodes.forEach(d => {
            d.y = d.depth * 180;
        });

        // Update nodes
        const node = this.g.selectAll('g.node')
            .data(nodes, d => d.id || (d.id = ++this.i));

        // Enter new nodes
        const nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${source.y0},${source.x0})`)
            .on('click', (event, d) => this.click(d))
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip())
            .on('contextmenu', (event, d) => this.showContextMenu(event, d));

        // Add circles for nodes
        nodeEnter.append('circle')
            .attr('r', 1e-6)
            .style('fill', d => d._children ? this.getLightColor(d) : this.getColor(d))
            .style('stroke-width', '2px')
            .style('stroke', d => this.getStrokeColor(d));

        // Add labels
        nodeEnter.append('text')
            .attr('dy', '.35em')
            .attr('x', d => d.children || d._children ? -13 : 13)
            .attr('text-anchor', d => d.children || d._children ? 'end' : 'start')
            .text(d => d.data.name)
            .style('fill-opacity', 1e-6)
            .style('font-size', '12px')
            .style('font-family', 'monospace');

        // Add OID labels if available
        nodeEnter.append('text')
            .attr('dy', '1.5em')
            .attr('x', d => d.children || d._children ? -13 : 13)
            .attr('text-anchor', d => d.children || d._children ? 'end' : 'start')
            .text(d => d.data.oid || '')
            .style('fill-opacity', 1e-6)
            .style('font-size', '10px')
            .style('fill', '#666');

        // Transition nodes to their new position
        const nodeUpdate = nodeEnter.merge(node);

        nodeUpdate.transition()
            .duration(this.duration)
            .attr('transform', d => `translate(${d.y},${d.x})`);

        nodeUpdate.select('circle')
            .attr('r', 8)
            .style('fill', d => d._children ? this.getLightColor(d) : this.getColor(d))
            .style('stroke', d => this.getStrokeColor(d))
            .attr('cursor', 'pointer');

        nodeUpdate.selectAll('text')
            .style('fill-opacity', 1);

        // Remove exiting nodes
        const nodeExit = node.exit().transition()
            .duration(this.duration)
            .attr('transform', d => `translate(${source.y},${source.x})`)
            .remove();

        nodeExit.select('circle')
            .attr('r', 1e-6);

        nodeExit.select('text')
            .style('fill-opacity', 1e-6);

        // Update links
        const link = this.g.selectAll('path.link')
            .data(links, d => d.target.id);

        // Enter new links
        const linkEnter = link.enter().insert('path', 'g')
            .attr('class', 'link')
            .attr('d', d => {
                const o = { x: source.x0, y: source.y0 };
                return this.diagonal(o, o);
            });

        // Transition links to their new position
        const linkUpdate = linkEnter.merge(link);

        linkUpdate.transition()
            .duration(this.duration)
            .attr('d', d => this.diagonal(d.source, d.target));

        // Remove exiting links
        link.exit().transition()
            .duration(this.duration)
            .attr('d', d => {
                const o = { x: source.x, y: source.y };
                return this.diagonal(o, o);
            })
            .remove();

        // Store old positions for transition
        nodes.forEach(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }

    diagonal(s, d) {
        const path = `M ${s.y} ${s.x}
                    C ${(s.y + d.y) / 2} ${s.x},
                      ${(s.y + d.y) / 2} ${d.x},
                      ${d.y} ${d.x}`;
        return path;
    }

    click(d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        this.update(d);
        this.onNodeClick(d);
    }

    onNodeClick(node) {
        // Trigger custom event
        const event = new CustomEvent('nodeClick', {
            detail: {
                node: node,
                data: node.data
            }
        });
        document.dispatchEvent(event);

        // Show node details
        this.showNodeDetails(node.data);
    }

    showNodeDetails(nodeData) {
        const detailsContainer = document.getElementById('node-details');
        if (detailsContainer) {
            let html = `
                <h6>${nodeData.name}</h6>
                <table class="table table-sm node-details-table">
            `;

            const fields = [
                { key: 'oid', label: 'OID', format: (v) => `<code>${v}</code>` },
                { key: 'description', label: 'Description' },
                { key: 'syntax', label: 'Syntax', format: (v) => `<code>${v}</code>` },
                { key: 'access', label: 'Access' },
                { key: 'status', label: 'Status' },
                { key: 'module', label: 'Module' },
                { key: 'text_convention', label: 'Text Convention' },
                { key: 'units', label: 'Units' },
                { key: 'max_access', label: 'Max Access' }
            ];

            fields.forEach(field => {
                if (nodeData[field.key]) {
                    const value = field.format ? field.format(nodeData[field.key]) : nodeData[field.key];
                    html += `
                        <tr>
                            <td><strong>${field.label}:</strong></td>
                            <td>${value}</td>
                        </tr>
                    `;
                }
            });

            html += '</table>';
            detailsContainer.innerHTML = html;
        }
    }

    showTooltip(event, d) {
        const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);

        tooltip.transition()
            .duration(200)
            .style('opacity', .9);

        let tooltipContent = `<strong>${d.data.name}</strong>`;
        if (d.data.oid) {
            tooltipContent += `<br/>OID: ${d.data.oid}`;
        }
        if (d.data.description) {
            const desc = d.data.description.length > 50 ?
                d.data.description.substring(0, 50) + '...' :
                d.data.description;
            tooltipContent += `<br/>${desc}`;
        }

        tooltip.html(tooltipContent)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');
    }

    hideTooltip() {
        d3.selectAll('.tooltip').remove();
    }

    showContextMenu(event, d) {
        event.preventDefault();
        // Implementation for context menu
        console.log('Context menu for:', d.data.name);
    }

    getColor(d) {
        if (!d.parent) return '#4CAF50'; // Root
        if (!d.children && !d._children) return '#FF9800'; // Leaf
        return '#2196F3'; // Branch
    }

    getLightColor(d) {
        if (!d.parent) return '#81C784'; // Root
        if (!d.children && !d._children) return '#FFB74D'; // Leaf
        return '#64B5F6'; // Branch
    }

    getStrokeColor(d) {
        return '#fff';
    }

    expandAll() {
        this.expand(this.root);
        this.update(this.root);
    }

    collapseAll() {
        this.root.children.forEach(this.collapse.bind(this));
        this.update(this.root);
    }

    resetZoom() {
        this.svg.transition()
            .duration(750)
            .call(
                d3.zoom().transform,
                d3.zoomIdentity.translate(this.margin.left, this.margin.top)
            );
    }

    search(query) {
        this.searchResults = [];
        const lowercaseQuery = query.toLowerCase();

        function searchNodes(node) {
            let found = false;

            if (node.data.name.toLowerCase().includes(lowercaseQuery) ||
                (node.data.oid && node.data.oid.toLowerCase().includes(lowercaseQuery)) ||
                (node.data.description && node.data.description.toLowerCase().includes(lowercaseQuery))) {
                found = true;
            }

            // Search children
            if (node.children) {
                node.children.forEach(child => {
                    if (searchNodes(child)) {
                        found = true;
                        // Expand path to found node
                        child._children = null;
                        child.children = child._children || child.children;
                    }
                });
            }

            if (node._children) {
                node._children.forEach(child => {
                    if (searchNodes(child)) {
                        found = true;
                    }
                });
            }

            if (found) {
                this.searchResults.push(node);
            }

            return found;
        }

        searchNodes.call(this, this.root);
        this.update(this.root);

        return this.searchResults;
    }

    highlightNode(nodeName) {
        // Reset previous highlights
        this.g.selectAll('.node circle')
            .classed('highlight', false);

        // Highlight matching node
        this.g.selectAll('.node')
            .filter(d => d.data.name === nodeName)
            .select('circle')
            .classed('highlight', true);
    }

    clearHighlights() {
        this.g.selectAll('.node circle')
            .classed('highlight', false);
    }

    switchLayout(layout) {
        this.currentLayout = layout;

        if (layout === 'radial') {
            this.setupRadialLayout();
        } else {
            this.setupTreeLayout();
        }

        this.update(this.root);
    }

    setupRadialLayout() {
        const diameter = Math.min(this.width, this.height);
        const radius = diameter / 2;

        this.tree = d3.tree()
            .size([2 * Math.PI, radius - 100])
            .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);

        // Update transform
        this.g.attr('transform', `translate(${this.width/2},${this.height/2})`);

        // Update diagonal function for radial
        this.diagonal = function(s, d) {
            return `M${s.y * Math.cos(s.x - Math.PI/2)},${s.y * Math.sin(s.x - Math.PI/2)}
                    C${(s.y + d.y) * Math.cos(s.x - Math.PI/2) / 2},${(s.y + d.y) * Math.sin(s.x - Math.PI/2) / 2}
                     ${(s.y + d.y) * Math.cos(d.x - Math.PI/2) / 2},${(s.y + d.y) * Math.sin(d.x - Math.PI/2) / 2}
                     ${d.y * Math.cos(d.x - Math.PI/2)},${d.y * Math.sin(d.x - Math.PI/2)}`;
        };
    }

    setupTreeLayout() {
        const treeWidth = this.width - this.margin.right - this.margin.left;
        const treeHeight = this.height - this.margin.top - this.margin.bottom;

        this.tree = d3.tree()
            .size([treeHeight, treeWidth]);

        // Update transform
        this.g.attr('transform', `translate(${this.margin.left},${this.margin.top})`);

        // Reset diagonal function
        this.diagonal = (s, d) => {
            const path = `M ${s.y} ${s.x}
                        C ${(s.y + d.y) / 2} ${s.x},
                          ${(s.y + d.y) / 2} ${d.x},
                          ${d.y} ${d.x}`;
            return path;
        };
    }

    exportSVG() {
        const svgElement = document.querySelector(`#${this.containerId} svg`);
        const svgString = new XMLSerializer().serializeToString(svgElement);
        return svgString;
    }

    resize() {
        this.setupDimensions();
        this.svg
            .attr('width', this.width)
            .attr('height', this.height);

        // Re-setup tree with new dimensions
        if (this.currentLayout === 'tree') {
            this.setupTreeLayout();
        } else {
            this.setupRadialLayout();
        }

        this.update(this.root);
    }
}

// Export for use in other scripts
window.TreeVisualization = TreeVisualization;