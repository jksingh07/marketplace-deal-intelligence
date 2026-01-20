# Architecture Documentation

## System Overview

Stage 4 Description Intelligence is a **LLM-primary extraction pipeline with deterministic guardrails** that converts raw listing text into structured, evidence-backed intelligence signals.

### Design Philosophy

1. **LLM is the Primary Extractor** - LLMs handle nuanced extraction and context understanding
2. **Guardrails Never Fail** - Rule-based patterns catch critical signals even if LLM fails
3. **Evidence is Required** - Every signal must be traceable to source text
4. **Schema-Valid Always** - Outputs always conform to JSON Schema contract
5. **Idempotent by Design** - Same inputs produce identical outputs
6. **Resilient by Design** - Unknown LLM outputs map to `"other"` instead of failing (prevents data loss)

---

## Pipeline Architecture

<svg aria-roledescription="flowchart-v2" role="graphics-document document" viewBox="-8 -8 361.9651794433594 953.5" style="max-width: 361.9651794433594px;" xmlns="http://www.w3.org/2000/svg" width="100%" id="mermaid-svg-1768729038986-fxbjxm9vy"><style>#mermaid-svg-1768729038986-fxbjxm9vy{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#333;}#mermaid-svg-1768729038986-fxbjxm9vy .error-icon{fill:#552222;}#mermaid-svg-1768729038986-fxbjxm9vy .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-1768729038986-fxbjxm9vy .edge-thickness-normal{stroke-width:2px;}#mermaid-svg-1768729038986-fxbjxm9vy .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-1768729038986-fxbjxm9vy .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-1768729038986-fxbjxm9vy .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-1768729038986-fxbjxm9vy .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-1768729038986-fxbjxm9vy .marker{fill:#333333;stroke:#333333;}#mermaid-svg-1768729038986-fxbjxm9vy .marker.cross{stroke:#333333;}#mermaid-svg-1768729038986-fxbjxm9vy svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-1768729038986-fxbjxm9vy .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#333;}#mermaid-svg-1768729038986-fxbjxm9vy .cluster-label text{fill:#333;}#mermaid-svg-1768729038986-fxbjxm9vy .cluster-label span,#mermaid-svg-1768729038986-fxbjxm9vy p{color:#333;}#mermaid-svg-1768729038986-fxbjxm9vy .label text,#mermaid-svg-1768729038986-fxbjxm9vy span,#mermaid-svg-1768729038986-fxbjxm9vy p{fill:#333;color:#333;}#mermaid-svg-1768729038986-fxbjxm9vy .node rect,#mermaid-svg-1768729038986-fxbjxm9vy .node circle,#mermaid-svg-1768729038986-fxbjxm9vy .node ellipse,#mermaid-svg-1768729038986-fxbjxm9vy .node polygon,#mermaid-svg-1768729038986-fxbjxm9vy .node path{fill:#ECECFF;stroke:#9370DB;stroke-width:1px;}#mermaid-svg-1768729038986-fxbjxm9vy .flowchart-label text{text-anchor:middle;}#mermaid-svg-1768729038986-fxbjxm9vy .node .label{text-align:center;}#mermaid-svg-1768729038986-fxbjxm9vy .node.clickable{cursor:pointer;}#mermaid-svg-1768729038986-fxbjxm9vy .arrowheadPath{fill:#333333;}#mermaid-svg-1768729038986-fxbjxm9vy .edgePath .path{stroke:#333333;stroke-width:2.0px;}#mermaid-svg-1768729038986-fxbjxm9vy .flowchart-link{stroke:#333333;fill:none;}#mermaid-svg-1768729038986-fxbjxm9vy .edgeLabel{background-color:#e8e8e8;text-align:center;}#mermaid-svg-1768729038986-fxbjxm9vy .edgeLabel rect{opacity:0.5;background-color:#e8e8e8;fill:#e8e8e8;}#mermaid-svg-1768729038986-fxbjxm9vy .labelBkg{background-color:rgba(232, 232, 232, 0.5);}#mermaid-svg-1768729038986-fxbjxm9vy .cluster rect{fill:#ffffde;stroke:#aaaa33;stroke-width:1px;}#mermaid-svg-1768729038986-fxbjxm9vy .cluster text{fill:#333;}#mermaid-svg-1768729038986-fxbjxm9vy .cluster span,#mermaid-svg-1768729038986-fxbjxm9vy p{color:#333;}#mermaid-svg-1768729038986-fxbjxm9vy div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(80, 100%, 96.2745098039%);border:1px solid #aaaa33;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-1768729038986-fxbjxm9vy .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#333;}#mermaid-svg-1768729038986-fxbjxm9vy :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}</style><g><marker orient="auto" markerHeight="12" markerWidth="12" markerUnits="userSpaceOnUse" refY="5" refX="6" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd"><path style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 0 0 L 10 5 L 0 10 z"/></marker><marker orient="auto" markerHeight="12" markerWidth="12" markerUnits="userSpaceOnUse" refY="5" refX="4.5" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointStart"><path style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 0 5 L 10 10 L 10 0 z"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5" refX="11" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1768729038986-fxbjxm9vy_flowchart-circleEnd"><circle style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" r="5" cy="5" cx="5"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5" refX="-1" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1768729038986-fxbjxm9vy_flowchart-circleStart"><circle style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" r="5" cy="5" cx="5"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5.2" refX="12" viewBox="0 0 11 11" class="marker cross flowchart" id="mermaid-svg-1768729038986-fxbjxm9vy_flowchart-crossEnd"><path style="stroke-width: 2; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 1,1 l 9,9 M 10,1 l -9,9"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5.2" refX="-1" viewBox="0 0 11 11" class="marker cross flowchart" id="mermaid-svg-1768729038986-fxbjxm9vy_flowchart-crossStart"><path style="stroke-width: 2; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 1,1 l 9,9 M 10,1 l -9,9"/></marker><g class="root"><g class="clusters"><g id="outputs" class="cluster default flowchart-label"><rect height="167.5" width="221.5234375" y="770" x="93.0713005065918" ry="0" rx="0" style=""/><g transform="translate(175.6591911315918, 770)" class="cluster-label"><foreignObject height="18.75" width="56.34765625"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Outputs</span></div></foreignObject></g></g><g id="stage4" class="cluster default flowchart-label"><rect height="586.25" width="345.96518325805664" y="133.75" x="0" ry="0" rx="0" style=""/><g transform="translate(115.80160331726074, 133.75)" class="cluster-label"><foreignObject height="18.75" width="114.36197662353516"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Stage 4 Pipeline</span></div></foreignObject></g></g><g id="inputs" class="cluster default flowchart-label"><rect height="83.75" width="207.40234375" y="0" x="100.1318473815918" ry="0" rx="0" style=""/><g transform="translate(181.99707984924316, 0)" class="cluster-label"><foreignObject height="18.75" width="43.671878814697266"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Inputs</span></div></foreignObject></g></g></g><g class="edgePaths"><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-RawJSON LE-TextPrep" id="L-RawJSON-TextPrep-0" d="M203.833,58.75L203.833,62.917C203.833,67.083,203.833,75.417,203.833,83.75C203.833,92.083,203.833,100.417,203.833,108.75C203.833,117.083,203.833,125.417,203.833,132.867C203.833,140.317,203.833,146.883,203.833,150.167L203.833,153.45"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-TextPrep LE-LLMExtract" id="L-TextPrep-LLMExtract-0" d="M176.452,192.5L169.692,196.667C162.931,200.833,149.41,209.167,142.649,216.617C135.889,224.067,135.889,230.633,135.889,233.917L135.889,237.2"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-LLMExtract LE-EvidenceVerify" id="L-LLMExtract-EvidenceVerify-0" d="M135.889,276.25L135.889,280.417C135.889,284.583,135.889,292.917,135.889,300.367C135.889,307.817,135.889,314.383,135.889,317.667L135.889,320.95"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-EvidenceVerify LE-GuardrailRules" id="L-EvidenceVerify-GuardrailRules-0" d="M135.889,360L135.889,364.167C135.889,368.333,135.889,376.667,141.897,384.537C147.906,392.406,159.923,399.813,165.932,403.516L171.941,407.219"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-TextPrep LE-GuardrailRules" id="L-TextPrep-GuardrailRules-0" d="M231.214,192.5L237.974,196.667C244.735,200.833,258.256,209.167,265.017,220.313C271.777,231.458,271.777,245.417,271.777,259.375C271.777,273.333,271.777,287.292,271.777,301.25C271.777,315.208,271.777,329.167,271.777,343.125C271.777,357.083,271.777,371.042,265.769,381.724C259.76,392.406,247.743,399.813,241.734,403.516L235.725,407.219"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-GuardrailRules LE-MergeNormalize" id="L-GuardrailRules-MergeNormalize-0" d="M203.833,443.75L203.833,447.917C203.833,452.083,203.833,460.417,203.833,467.867C203.833,475.317,203.833,481.883,203.833,485.167L203.833,488.45"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-MergeNormalize LE-DerivedFields" id="L-MergeNormalize-DerivedFields-0" d="M203.833,527.5L203.833,531.667C203.833,535.833,203.833,544.167,203.833,551.617C203.833,559.067,203.833,565.633,203.833,568.917L203.833,572.2"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-DerivedFields LE-OutputAssembly" id="L-DerivedFields-OutputAssembly-0" d="M203.833,611.25L203.833,615.417C203.833,619.583,203.833,627.917,203.833,635.367C203.833,642.817,203.833,649.383,203.833,652.667L203.833,655.95"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-OutputAssembly LE-SchemaValid" id="L-OutputAssembly-SchemaValid-0" d="M203.833,695L203.833,699.167C203.833,703.333,203.833,711.667,203.833,720C203.833,728.333,203.833,736.667,203.833,745C203.833,753.333,203.833,761.667,203.833,769.117C203.833,776.567,203.833,783.133,203.833,786.417L203.833,789.7"/><path marker-end="url(#mermaid-svg-1768729038986-fxbjxm9vy_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-SchemaValid LE-Storage" id="L-SchemaValid-Storage-0" d="M203.833,828.75L203.833,832.917C203.833,837.083,203.833,845.417,203.833,852.867C203.833,860.317,203.833,866.883,203.833,870.167L203.833,873.45"/></g><g class="edgeLabels"><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g><g class="edgeLabel"><g transform="translate(0, 0)" class="label"><foreignObject height="0" width="0"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel"></span></div></foreignObject></g></g></g><g class="nodes"><g transform="translate(203.8330192565918, 811.875)" id="flowchart-SchemaValid-41" class="node default default flowchart-label"><rect height="33.75" width="151.5234375" y="-16.875" x="-75.76171875" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-68.26171875, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="136.5234375"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Schema-Valid JSON</span></div></foreignObject></g></g><g transform="translate(203.8330192565918, 895.625)" id="flowchart-Storage-42" class="node default default flowchart-label"><rect height="33.75" width="92.6953125" y="-16.875" x="-46.34765625" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-38.84765625, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="77.6953125"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">DB Storage</span></div></foreignObject></g></g><g transform="translate(203.8330192565918, 175.625)" id="flowchart-TextPrep-34" class="node default default flowchart-label"><rect height="33.75" width="133.50260162353516" y="-16.875" x="-66.75130081176758" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-59.25130081176758, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="118.50260162353516"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Text Preparation</span></div></foreignObject></g></g><g transform="translate(135.88867950439453, 259.375)" id="flowchart-LLMExtract-35" class="node default default flowchart-label"><rect height="33.75" width="201.77735900878906" y="-16.875" x="-100.88867950439453" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-93.38867950439453, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="186.77735900878906"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">LLM Structured Extraction</span></div></foreignObject></g></g><g transform="translate(135.88867950439453, 343.125)" id="flowchart-EvidenceVerify-36" class="node default default flowchart-label"><rect height="33.75" width="166.73828125" y="-16.875" x="-83.369140625" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-75.869140625, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="151.73828125"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Evidence Verification</span></div></foreignObject></g></g><g transform="translate(203.8330192565918, 426.875)" id="flowchart-GuardrailRules-37" class="node default default flowchart-label"><rect height="33.75" width="158.69790649414062" y="-16.875" x="-79.34895324707031" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-71.84895324707031, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="143.69790649414062"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Guardrail Rules Pass</span></div></foreignObject></g></g><g transform="translate(203.8330192565918, 510.625)" id="flowchart-MergeNormalize-38" class="node default default flowchart-label"><rect height="33.75" width="166.0677032470703" y="-16.875" x="-83.03385162353516" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-75.53385162353516, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="151.0677032470703"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Merge and Normalize</span></div></foreignObject></g></g><g transform="translate(203.8330192565918, 594.375)" id="flowchart-DerivedFields-39" class="node default default flowchart-label"><rect height="33.75" width="186.7512969970703" y="-16.875" x="-93.37564849853516" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-85.87564849853516, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="171.7512969970703"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Derived Summary Fields</span></div></foreignObject></g></g><g transform="translate(203.8330192565918, 678.125)" id="flowchart-OutputAssembly-40" class="node default default flowchart-label"><rect height="33.75" width="134.7265625" y="-16.875" x="-67.36328125" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-59.86328125, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="119.7265625"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Output Assembly</span></div></foreignObject></g></g><g transform="translate(203.8330192565918, 41.875)" id="flowchart-RawJSON-33" class="node default default flowchart-label"><rect height="33.75" width="137.40234375" y="-16.875" x="-68.701171875" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-61.201171875, -9.375)" style="" class="label"><rect/><foreignObject height="18.75" width="122.40234375"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Raw Listing JSON</span></div></foreignObject></g></g></g></g></g></svg>



### High-Level Flow

```
Raw Listing (title + description)
    │
    ├─→ [Text Preparation]
    │      │
    │      ├─→ Normalize text (whitespace, casing)
    │      ├─→ Split into sentences
    │      └─→ Preserve original for evidence matching
    │
    ├─→ [Guardrail Rules] ─────┐
    │      │                   │
    │      └─→ Pattern matching │ (ALWAYS RUNS)
    │          (write-off,      │
    │           defected,       │
    │           stage 2, etc.)  │
    │                           │
    └─→ [LLM Extraction] ───────┤
         │                      │
         └─→ OpenAI API call    │
             Structured JSON    │
                                │
                                ▼
                    [Evidence Verification]
                         │
                         ├─→ Check evidence_text exists verbatim
                         ├─→ Reject hallucinations
                         └─→ Classify verified vs inferred
                                │
                                ▼
                         [Signal Merger]
                         │
                         ├─→ Combine LLM + guardrail signals
                         ├─→ Deduplicate by (type, evidence)
                         └─→ Prefer guardrail confidence on conflicts
                                │
                                ▼
                         [Derived Fields]
                         │
                         ├─→ risk_level_overall
                         ├─→ mods_risk_level
                         ├─→ negotiation_stance
                         └─→ service_history_level
                                │
                                ▼
                         [Schema Validation]
                         │
                         └─→ Ensure JSON Schema compliance
                                │
                                ▼
                    Final Output (Stage 4 JSON)
```

---

## Component Architecture

### 1. Text Preparation (`text_prep.py`)

**Purpose:** Normalize and prepare text for extraction while preserving original for evidence.

**Key Functions:**
- `normalize_text()` - Combines title + description, normalizes whitespace
- `split_sentences()` - Tokenizes text into sentences for evidence extraction
- `find_evidence_span()` - Extracts context around keywords for evidence

**Design Decisions:**
- Preserves original casing for evidence matching
- Lowercases normalized version for pattern matching
- Sentence splitting enables precise evidence spans

### 2. Guardrail Rules (`guardrails.py`)

**Purpose:** Deterministic pattern matching for high-severity signals.

**Coverage:**
- **Legality:** defected, unregistered, no rego, no RWC
- **Accident History:** write-off, salvage, flood damage
- **Mechanical:** not running, overheating, engine knock
- **Performance Mods:** stage 2+, E85, turbo swap, track use
- **Seller Behavior:** firm price, urgent sale

**Properties:**
- Always `verification_level=verified`
- Always `confidence=0.95`
- Evidence text is exact substring match
- Never removed by LLM output (rules win conflicts)

### 3. LLM Extractor (`llm_extractor.py`)

**Purpose:** Structured extraction using OpenAI GPT models.

**Features:**
- Loads prompt from `stages/stage4_description_intel/prompts/extractor_prompt.md`
- Retries with exponential backoff (3 attempts)
- Handles malformed JSON gracefully
- Falls back to minimal structure if LLM fails

**Output Structure:**
- Matches Stage 4 schema exactly
- All signals have evidence_text
- All enums match contract definitions

### 4. Evidence Verifier (`evidence_verifier.py`)

**Purpose:** Validate that all signals have verbatim evidence in source text.

**Verification Rules:**
- Evidence text must exist in original text (case-insensitive)
- Rejects signals without valid evidence
- Classifies as `verified` (explicit) or `inferred` (implicit wording)
- Adjusts confidence based on verification level

**Safety:** Prevents hallucination by requiring exact substring matches.

### 5. Signal Merger (`merger.py`)

**Purpose:** Combine LLM and guardrail signals without duplicates.

**Merge Strategy:**
- Union both signal sets
- Deduplicate by `(type, evidence_text)`
- If conflict: Prefer guardrail signal (higher confidence)
- Preserve verification levels from both sources

**Maintenance:** Deduplicates claims and red flags separately.

### 6. Derived Fields (`derived_fields.py`)

**Purpose:** Compute summary fields from extracted signals (rule-based, not LLM).

**Computed Fields:**

| Field | Logic |
|-------|-------|
| `risk_level_overall` | HIGH if any HIGH severity verified; MEDIUM if multiple medium; LOW otherwise |
| `mods_risk_level` | HIGH: stage 2+, turbo swap, E85, track use; MEDIUM: tuned, intake/exhaust; LOW: cosmetic |
| `service_history_level` | FULL: logbook + receipts; PARTIAL: claims without proof; NONE: explicit "no history" |
| `negotiation_stance` | FIRM: "firm price", "no lowballers"; OPEN: "negotiable", "need gone" |
| `claimed_condition` | EXCELLENT → GOOD → FAIR → NEEDS_WORK based on signals |

**Design:** Deterministic computations ensure idempotency.

### 7. Schema Validator (`schema_validator.py`)

**Purpose:** Validate final output against JSON Schema contract.

**Validation:**
- Loads schema from `contracts/stage4_description_intel.schema.json`
- Validates all required fields present
- Validates enum values match schema
- Validates confidence in [0, 1]
- Validates evidence_text non-empty

**On Failure:** Raises detailed error with field paths and messages.

### 8. Pipeline Runner (`runner.py`)

**Purpose:** Orchestrate all stages in correct order.

**Pipeline Steps:**
1. Extract listing fields (with defaults)
2. Text preparation
3. LLM extraction (or fallback)
4. Evidence verification
5. Guardrail rules
6. Signal merging
7. Derived field computation
8. Build final output structure
9. Schema validation (optional)

**Idempotency:** Same listing + snapshot_id = identical output structure.

---

## Data Flow

### Input Format

```python
listing = {
    "listing_id": "12345",
    "title": "2015 Subaru WRX STI",
    "description": "Stage 2 tune, defected for exhaust...",
    "vehicle_type": "car",  # Optional, defaults to "unknown"
    "price": 25000,  # Optional
    "mileage": 50000,  # Optional
}
```

### Output Format

```json
{
  "listing_id": "12345",
  "source_snapshot_id": "12345",
  "created_at": "2024-01-18T12:00:00Z",
  "stage_name": "stage4_description_intelligence",
  "stage_version": "v1.0.0",
  "ruleset_version": "v1.0",
  "llm_version": "gpt-4o-mini",
  "payload": {
    "risk_level_overall": "high",
    "negotiation_stance": "open",
    "claimed_condition": "fair",
    "service_history_level": "unknown",
    "mods_risk_level": "high",
    "signals": {
      "legality": [{...}],
      "accident_history": [{...}],
      "mechanical_issues": [{...}],
      "cosmetic_issues": [{...}],
      "mods_performance": [{...}],
      "mods_cosmetic": [{...}],
      "seller_behavior": [{...}]
    },
    "maintenance": {
      "claims": [...],
      "evidence_present": [...],
      "red_flags": [...]
    },
    "missing_info": [...],
    "follow_up_questions": [...],
    "extraction_warnings": [...],
    "source_text_stats": {...}
  }
}
```

---

## Design Patterns

### 1. Guardrail-First Safety

Guardrails **always run** regardless of LLM status. This ensures:
- Critical signals (write-off, defected) are never missed
- Pipeline works even if LLM is unavailable
- High-severity patterns have 100% detection rate

### 2. Evidence-Based Verification

Every signal requires verbatim evidence text:
- Prevents hallucination
- Enables traceability
- Supports confidence scoring

### 3. Deterministic Merging

Merge logic is rule-based:
- No randomness in signal combination
- Idempotent output structure
- Predictable conflict resolution (rules win)

### 4. Fail-Safe Fallbacks

- LLM fails → Return rules-only output
- Invalid JSON → Return minimal valid structure
- Schema validation → Raise clear error (don't mask)

### 5. Schema-Driven Development

- Output contract defined in JSON Schema
- Code validates against schema
- Schema changes trigger validation updates

---

## Performance Characteristics

### Latency (Guardrails-Only)

- Text prep: < 1ms
- Guardrail rules: < 5ms
- Derived fields: < 1ms
- Schema validation: < 10ms
- **Total: < 20ms per listing**

### Latency (With LLM)

- LLM API call: 1-3 seconds (depending on model)
- Evidence verification: < 10ms
- Other steps: same as guardrails-only
- **Total: 1-3 seconds per listing**

### Throughput

- Guardrails-only: ~50 listings/second (CPU-bound)
- With LLM: Limited by OpenAI rate limits (varies by tier)

---

## Error Handling

### LLM Failures

- Timeout/rate limit → Retry 3x with exponential backoff
- Invalid JSON → Return fallback structure with warning
- API error → Return rules-only output

### Validation Failures

- Schema mismatch → Raise `ValidationError` with details
- Missing fields → Fail fast with clear message
- Invalid enums → Validation error with field path

### Evidence Failures

- Missing evidence → Signal rejected (not in output)
- Partial match → Treated as inferred (lower confidence)

---

## Extensibility

### Adding New Guardrail Rules

Edit `src/stage4/guardrails.py`:

```python
NEW_RULE = (r'\bnew_pattern\b', 'signal_type', 'category', 'severity')
ALL_RULES = ALL_RULES + [NEW_RULE]
```

### Adding New Signal Types

1. Add enum to `src/common/models.py`
2. Update schema in `contracts/stage4_description_intel.schema.json`
3. Update prompt template if LLM should extract it

### Adding New Derived Fields

Edit `src/stage4/derived_fields.py`:

```python
def compute_new_field(signals, ...) -> str:
    # Deterministic logic
    return "value"
```

Then add to `compute_derived_fields()` return dict.

---

## Security Considerations

### API Key Management

- `OPENAI_API_KEY` loaded from environment variable
- Never logged or exposed in outputs
- Use `.env` file locally (gitignored)

### Input Validation

- Sanitize listing text (prevent injection)
- Validate listing_id format
- Limit input text length (prevent DoS)

### Output Sanitization

- All outputs are JSON (structured)
- No executable code in outputs
- Evidence text is verbatim from input (no code injection)

---

## Production-Ready Modules

The pipeline includes the following production-hardened modules:

### 1. Centralized Enums (`common/schema_enums.py`)

Single source of truth for all enum definitions, loaded dynamically from the JSON schema.
Prevents drift between schema and code.

### 2. Signal Normalizer (`stage4/normalizer.py`)

Gracefully handles LLM output variations by mapping common alternatives to valid schema values.
**Key Design Principle**: Unknown types map to `"other"` instead of being rejected, ensuring no data loss.

**Examples:**
- `"write_off"` → `"writeoff"`
- `"service_history"` → `"logbook"`
- `"service_history_none"` → `"service_history_unknown"`
- `"rwc_status_unknown"` → `"other"` (preserved, not rejected)

**Architectural Benefit**: Makes the system resilient to LLM variations without breaking production.

### 3. Structured Logging (`common/logging_config.py`)

JSON-structured logging for production environments, with human-readable format for development.

### 4. Metrics Collection (`common/metrics.py`)

Thread-safe metrics collection for monitoring:
- Counters, gauges, histograms, timers
- Per-extraction metrics (latency, tokens, signals)
- Ready for Prometheus/DataDog integration

### 5. Rate Limiting (`common/rate_limiter.py`)

Token bucket rate limiter for API calls:
- Configurable calls per minute/second
- Burst support
- Async support

### 6. Circuit Breaker (`common/circuit_breaker.py`)

Prevents cascading failures when external services are down:
- CLOSED → OPEN → HALF_OPEN state machine
- Configurable thresholds and timeouts
- Sync and async support

### 7. Result Caching (`common/caching.py`)

LRU cache with TTL for expensive operations:
- Guardrails cache (24hr TTL, deterministic)
- LLM cache (1hr TTL)
- Thread-safe

### 8. Input Validation (`common/input_validation.py`)

Validates and sanitizes input before processing:
- Length limits (prevent DoS)
- Required field checks
- Content sanitization

### 9. Async LLM (`stage4/llm_extractor_async.py`)

Non-blocking LLM extraction for concurrent processing:
- AsyncOpenAI client
- Batch extraction with semaphore-controlled concurrency

---

## Resilient Design Pattern

### Problem Solved

**Original Issue**: LLMs are probabilistic and produce variations. Strict enum validation caused:
- Validation failures on unknown types
- Data loss when LLM used valid semantic variations
- Production instability with new LLM outputs
- Rigid system that broke on edge cases

### Solution: "Other" Fallback Pattern

**All enum types include `"other"` as a valid value:**
- `signal_legality_type`: includes `"other"`
- `signal_accident_type`: includes `"other"`
- `signal_mechanical_type`: includes `"other"`
- `maintenance_claim_type`: includes `"other"`
- `maintenance_red_flag_type`: includes `"other"`
- `missing_info`: includes `"other"`

**Normalization Layer:**
- Maps known variations to valid types (e.g., `"write_off"` → `"writeoff"`)
- Maps unknown types to `"other"` instead of rejecting
- Preserves all valid semantic content from LLM

**Result**: 
- ✅ No data loss from LLM variations
- ✅ Production stability with unexpected inputs
- ✅ Graceful degradation without breaking
- ✅ System handles any LLM output

**Trade-off**: Some signals may be categorized as `"other"`, but this is preferable to losing all information.

---

## Current Implementation Status

### ✅ Completed

1. **JSON Mode**: Using OpenAI JSON mode for structured responses
2. **Async Support**: Async LLM extraction for concurrent processing
3. **Structured Logging**: JSON logs for production environments
4. **Metrics Collection**: Thread-safe metrics for monitoring
5. **Rate Limiting**: Token bucket rate limiter
6. **Circuit Breaker**: Failure handling with state machine
7. **Result Caching**: LRU cache with TTL
8. **Input Validation**: Sanitization and validation
9. **Resilient Normalization**: Unknown types → "other" pattern
10. **Centralized Enums**: Single source of truth from schema

### 🚧 Future Enhancements

1. **OpenAI Structured Outputs (Strict)**: Use strict JSON schema mode when available
2. **A/B Testing**: Compare LLM models for quality
3. **Distributed Caching**: Redis integration for multi-instance deployments
4. **Prompt Versioning**: Track prompt versions for reproducibility
5. **Model Fallback Chain**: Automatic fallback to cheaper models on errors
6. **Batch Optimization**: Optimize token usage with batching strategies

---

## Related Documentation

- **Code Details:** See `CODE_DOCUMENTATION.md`
- **Testing:** See `TESTING.md`
- **Contributing:** See `CONTRIBUTING.md`
- **Stage Contracts:** See `docs/STAGE_OUTPUT_CONTRACTS.md`
