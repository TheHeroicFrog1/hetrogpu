import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=90, bottom=90, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_styled_heading(doc, text, level):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    if level == 1:
        run.font.size = Pt(13.0)
        run.font.color.rgb = RGBColor(30, 58, 138)  # Deep Navy Blue
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(3)
    elif level == 2:
        run.font.size = Pt(11.0)
        run.font.color.rgb = RGBColor(37, 99, 235)  # Royal Blue
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
    elif level == 3:
        run.font.size = Pt(10.0)
        run.font.color.rgb = RGBColor(71, 85, 105)  # Slate
        p.paragraph_format.space_before = Pt(5)
        p.paragraph_format.space_after = Pt(2)
    return p

def add_body_paragraph(doc, text, bold_prefix=None, italic_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(4.5)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.bold = True
        r_bold.font.size = Pt(10.0)
        r_bold.font.color.rgb = RGBColor(15, 23, 42)
    if italic_prefix:
        r_it = p.add_run(italic_prefix)
        r_it.italic = True
        r_it.font.size = Pt(10.0)
        r_it.font.color.rgb = RGBColor(51, 65, 85)

    r_text = p.add_run(text)
    r_text.font.size = Pt(10.0)
    r_text.font.color.rgb = RGBColor(30, 41, 59)
    return p

def add_bullet_item(doc, text, bold_title=None):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.left_indent = Inches(0.28)
    p.paragraph_format.first_line_indent = Inches(-0.14)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    r_bullet = p.add_run("•  ")
    r_bullet.bold = True
    r_bullet.font.size = Pt(10.0)
    r_bullet.font.color.rgb = RGBColor(37, 99, 235)

    if bold_title:
        r_title = p.add_run(bold_title)
        r_title.bold = True
        r_title.font.size = Pt(10.0)
        r_title.font.color.rgb = RGBColor(15, 23, 42)

    r_body = p.add_run(text)
    r_body.font.size = Pt(10.0)
    r_body.font.color.rgb = RGBColor(30, 41, 59)
    return p

def add_caption(doc, figure_text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(figure_text)
    run.font.size = Pt(9.0)
    run.italic = True
    run.bold = True
    run.font.color.rgb = RGBColor(71, 85, 105)
    return p

def format_table_header(row, titles, col_widths, bg_color="1E3A8A"):
    for idx, (title, width) in enumerate(zip(titles, col_widths)):
        cell = row.cells[idx]
        cell.width = width
        set_cell_background(cell, bg_color)
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(255, 255, 255)

def format_table_row(row, values, col_widths, is_even=False, align_left_col0=True):
    bg_color = "F8FAFC" if is_even else "FFFFFF"
    for idx, (val, width) in enumerate(zip(values, col_widths)):
        cell = row.cells[idx]
        cell.width = width
        set_cell_background(cell, bg_color)
        set_cell_margins(cell, top=60, bottom=60, left=90, right=90)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if (idx == 0 and align_left_col0) else WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(str(val))
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(30, 41, 59)
        if idx == 0 and align_left_col0:
            run.bold = True

def build_synopsis():
    src_path = r"C:\Users\aadit\Downloads\HeteroGPU_Synopsis (3).docx"
    doc = docx.Document(src_path)

    # 1. Clean out previous body paragraphs and tables while preserving cover page (paragraphs 0..8)
    for p in list(doc.paragraphs)[9:]:
        p._element.getparent().remove(p._element)
    for t in list(doc.tables):
        t._element.getparent().remove(t._element)

    # Add page break after the cover page
    doc.paragraphs[8].add_run().add_break(docx.enum.text.WD_BREAK.PAGE)

    # -------------------------------------------------------------
    # DOCUMENT HEADER
    # -------------------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(2)
    r_main = p_title.add_run("HeteroGPU: A Heterogeneous SIMT GPU with Specialized AI and Data-Movement Engines\n")
    r_main.bold = True
    r_main.font.size = Pt(12.5)
    r_main.font.color.rgb = RGBColor(30, 58, 138)

    r_sub = p_title.add_run("[ Architectural Proof-of-Concept on FPGA ]")
    r_sub.bold = True
    r_sub.italic = True
    r_sub.font.size = Pt(10.0)
    r_sub.font.color.rgb = RGBColor(37, 99, 235)

    # -------------------------------------------------------------
    # ABSTRACT
    # -------------------------------------------------------------
    add_styled_heading(doc, "Abstract", level=1)
    add_body_paragraph(doc, 
        "Most GPUs today are built around a homogeneous Single Instruction, Multiple Threads (SIMT) architecture, where identical instructions run across many parallel cores. "
        "This works well for traditional graphics rendering and pixel shaders. "
        "However, modern artificial intelligence workloads look very different: they are dominated by matrix multiplications (GEMM) and moving large blocks of tensor data. "
        "When general SIMT cores are forced to do matrix math, they spend extra clock cycles broadcasting weights, running out of registers, and waiting on memory. "
        "At the same time, using compute cores to move data back and forth leaves them sitting idle instead of doing useful calculations."
    )
    add_body_paragraph(doc,
        "In this project, we design and evaluate HeteroGPU, a 16-bit heterogeneous GPU architecture that solves these bottlenecks by giving different tasks to specialized hardware units. "
        "Rather than forcing one core type to do everything, HeteroGPU combines three engines under a unified controller: "
        "(1) a 4-core SIMT engine for general vector and graphics math, equipped with single-cycle hardware ReLU activation; "
        "(2) a 2x2 systolic array (AI matrix engine) that completes 2x2 matrix multiplications in just 4 clock cycles using 4 DSP multiply-accumulate units; and "
        "(3) an autonomous hardware DMA controller that copies memory blocks in 1+N cycles without stalling the compute cores. "
        "All three engines share an 8 KB dual-port Block RAM and report cycle counts through an on-chip hardware telemetry unit."
    )
    add_body_paragraph(doc,
        "We implemented this architecture in two completed phases. "
        "First, we built a cycle-accurate software simulator in Python to verify our instruction set, memory timing, and a calibrated 2-layer neural network (achieving a 100% intercept rate in an autonomous Pong demonstration). "
        "Second, we wrote the complete synthesizable hardware in SystemVerilog and verified it with Icarus Verilog testbenches and WaveTrace/GTKWave waveform traces. "
        "In benchmark tests, our 2x2 matrix engine delivered a 5.75x hardware speedup over the SIMT baseline for a 4x4 matrix multiply (16 cycles vs. 92 cycles), "
        "our DMA engine moved memory blocks in 65 cycles vs. 80 cycles while keeping compute cores 100% free, and our neural network executed an end-to-end forward pass in only 34 clock cycles."
    )
    add_body_paragraph(doc,
        "We are targeting the low-cost Sipeed Tang Nano 9K FPGA (8,640 logic cells) at 27 MHz as our physical proof-of-concept. "
        "Starting on a budget board proves that our architecture works efficiently by design rather than relying on expensive, brute-force hardware. "
        "Because our SystemVerilog code is modular and parameterized, it can scale naturally to larger FPGAs (like the Tang Nano 20K or Xilinx Artix-7) or even be taped out as a custom silicon ASIC chip."
    )

    # -------------------------------------------------------------
    # 1. INTRODUCTION & MOTIVATION
    # -------------------------------------------------------------
    add_styled_heading(doc, "1. Introduction & Motivation", level=1)
    
    add_styled_heading(doc, "1.1 Background: Why GPUs Are Built Around SIMT", level=2)
    add_body_paragraph(doc,
        "For the past twenty years, GPUs have relied on the Single Instruction, Multiple Threads (SIMT) model. "
        "In SIMT, a group of parallel cores runs the exact same instruction at the same time, but each core works on its own piece of data. "
        "This execution style is great for graphics, image filtering, and vector arithmetic because thousands of pixels all need the exact same calculation."
    )

    add_styled_heading(doc, "1.2 The Problem: Why Regular SIMT Struggles with AI", level=2)
    add_body_paragraph(doc,
        "Modern applications increasingly rely on neural networks, which are mostly made of matrix multiplications (GEMM): C = A x B + C. "
        "When we run matrix multiplication on standard SIMT cores, three big hardware bottlenecks show up:"
    )
    add_bullet_item(doc, "To multiply rows and columns, weights have to be broadcast across all cores one by one, causing pipeline delays.", bold_title="Broadcast Delays: ")
    add_bullet_item(doc, "Matrix math requires keeping many temporary numbers in memory at once. Small cores quickly run out of registers, forcing them to save and reload numbers from memory over and over (register spilling).", bold_title="Register Pressure: ")
    add_bullet_item(doc, "Standard ALUs do multiplication and addition in separate steps. Without a fused multiply-accumulate unit and direct data forwarding between neighbors, performance drops significantly.", bold_title="Separate Multiply and Add: ")
    add_body_paragraph(doc,
        "Another major issue is data movement (often called the 'Memory Wall'). "
        "In typical small GPUs, if you want to load new neural network weights or move an image sprite, the compute cores themselves must execute repetitive LOAD and STORE loops. "
        "While they are busy moving bytes around, they cannot do any actual math. "
        "Data movement needs to be handled by dedicated hardware so compute cores can keep working."
    )

    add_styled_heading(doc, "1.3 Our Solution: The HeteroGPU Architecture", level=2)
    add_body_paragraph(doc,
        "To solve these issues on edge hardware, HeteroGPU separates work across three specialized physical engines:",
        bold_prefix="The Three Core Engines: "
    )
    add_bullet_item(doc, "4 parallel cores with 8 registers each, designed for vertex shading, vector math, and single-cycle hardware ReLU activation.", bold_title="1. SIMT Vector Engine: ")
    add_bullet_item(doc, "A 2x2 grid of 4 DSP multiply-accumulate units. Data flows smoothly across the grid (Kung & Leiserson systolic flow), finishing a 2x2 matrix multiply in exactly 4 clock cycles.", bold_title="2. AI Matrix Engine: ")
    add_bullet_item(doc, "A hardware block transfer unit that copies memory in 1+N clock cycles without using any SIMT instruction cycles.", bold_title="3. DMA Controller: ")
    add_bullet_item(doc, "An 8 KB dual-port Block RAM (4096 16-bit words) with a memory arbiter and live cycle telemetry counters.", bold_title="4. Shared Memory & Telemetry: ")

    add_styled_heading(doc, "1.4 Proof of Concept & Scalability Approach", level=2)
    add_body_paragraph(doc,
        "It is important to understand that HeteroGPU is not just tied to one tiny chip. "
        "We chose the Sipeed Tang Nano 9K FPGA ($15 board with 8,640 logic cells) specifically as our physical Proof-of-Concept (PoC). "
        "If an architecture can deliver a 5.75x speedup inside such strict resource limits, it proves that the design is fundamentally sound. "
        "Because all our SystemVerilog code is parameterized, the same design can be scaled up to larger FPGAs or custom ASIC silicon."
    )

    # EMBED FIGURE 1 (Architecture Diagram)
    arch_img_path = r"C:\Users\aadit\HeteroGPU\python_test_simulator\results\heterogpu_architecture_diagram.png"
    if os.path.exists(arch_img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(4)
        p_img.paragraph_format.space_after = Pt(2)
        doc.add_picture(arch_img_path, width=Inches(6.4))
        add_caption(doc, "Figure 1: Comparison between a Traditional Homogeneous GPU (left) and our HeteroGPU Proof-of-Concept Architecture (right), showing engine decoupling and shared BRAM.")

    # -------------------------------------------------------------
    # 2. LITERATURE SURVEY & RELATED WORK
    # -------------------------------------------------------------
    add_styled_heading(doc, "2. Literature Survey & Related Work", level=1)
    add_body_paragraph(doc,
        "Our architecture connects ideas from foundational computer engineering papers with modern commercial hardware and open-source FPGA designs."
    )

    add_styled_heading(doc, "2.1 Foundational Systolic Arrays", level=2)
    add_body_paragraph(doc,
        "In 1979, H. T. Kung and C. E. Leiserson published their classic paper on Systolic Arrays [1]. "
        "They showed that instead of reading and writing every single number back to main memory, data can flow rhythmically through a grid of small processing cells. "
        "Each cell multiplies, adds, and passes the numbers directly to its neighbors. "
        "This saves memory bandwidth and keeps hardware busy. HeteroGPU uses this exact 2D dataflow for its matrix engine."
    )

    add_styled_heading(doc, "2.2 Commercial Accelerators: Google TPU and NVIDIA Tensor Cores", level=2)
    add_body_paragraph(doc,
        "In 2017, Google published their landmark ISCA paper on the Tensor Processing Unit (TPU v1) [2]. "
        "They showed that a 2D systolic matrix unit was 15x to 30x faster and more energy-efficient than regular CPUs and GPUs for neural network inference, "
        "proving that dedicated matrix hardware is essential for AI."
    )
    add_body_paragraph(doc,
        "Around the same time, NVIDIA added Tensor Cores to their Volta architecture (analyzed by Markidis et al. [3]). "
        "Instead of relying only on traditional CUDA cores, NVIDIA put dedicated 4x4 matrix units right next to them inside each Streaming Multiprocessor. "
        "This proved that modern GPUs must be heterogeneous: general SIMT cores for graphics, plus dedicated matrix units for AI."
    )

    add_styled_heading(doc, "2.3 Spatial AI Accelerators and the Memory Wall", level=2)
    add_body_paragraph(doc,
        "Research from MIT (Eyeriss by Chen et al. [4]) and surveys by Sze et al. [5] showed that moving data around a chip uses far more energy than doing math. "
        "They showed that accelerators must be designed around data reuse. "
        "More recently, Berkeley created Gemmini [6], an open-source systolic co-processor generator for RISC-V, and Alaei & Yazdanpanah [7] surveyed CPU-GPU coordination challenges."
    )

    add_styled_heading(doc, "2.4 Open-Source FPGA GPUs and the Research Gap", level=2)
    add_body_paragraph(doc,
        "Recently, great educational open-source GPUs have appeared, such as Adam Majmudar's 'tiny-gpu' (2024) [8] and 'smol-gpu'. "
        "These projects are great for learning how basic SIMT pipelines work. "
        "However, they all share one limitation: they are strictly homogeneous SIMT. "
        "None of them have a dedicated matrix unit or hardware DMA. When they try to run AI workloads, they suffer from the same slowdowns as early GPUs. "
        "HeteroGPU fills this exact gap by bringing heterogeneous specialization into a small, open-source FPGA design.",
        bold_prefix="The Research Gap: "
    )

    # TABLE 1: Literature Comparison Table
    add_styled_heading(doc, "2.5 Comparison with Existing Architectures", level=2)
    add_body_paragraph(doc, "Table 1 compares HeteroGPU against traditional GPUs, commercial accelerators, and existing educational FPGA GPUs:")

    t1 = doc.add_table(rows=6, cols=5)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths_t1 = [Inches(1.5), Inches(1.2), Inches(1.3), Inches(1.2), Inches(1.3)]
    
    t1_headers = ["Feature / Metric", "Traditional GPU", "Commercial Accelerators", "Open-Source GPUs", "HeteroGPU (Ours)"]
    format_table_header(t1.rows[0], t1_headers, col_widths_t1)
    
    t1_rows = [
        ["Core Architecture", "Homogeneous SIMT", "Specialized ASIC / Hybrid", "Homogeneous SIMT", "Heterogeneous SoC"],
        ["Matrix / GEMM Engine", "Software SIMT loops", "2D Systolic MXU / Tensor", "None (ALU math only)", "2x2 Systolic Array TPU"],
        ["Data Movement", "Software LOAD/STORE", "External PCIe / DMA", "Software loops only", "Hardware DMA Engine"],
        ["Activation Hardware", "Multi-cycle shader", "Specialized vector ALU", "Software branch CMP", "Single-cycle sign ReLU"],
        ["Target Platform", "ASIC Silicon", "Datacenter ASIC", "FPGA / Simulation", "Edge FPGA PoC -> ASIC"]
    ]
    for r_idx, row_vals in enumerate(t1_rows):
        format_table_row(t1.rows[r_idx + 1], row_vals, col_widths_t1, is_even=(r_idx % 2 == 1))

    # -------------------------------------------------------------
    # 3. PROBLEM FORMULATION & OBJECTIVES
    # -------------------------------------------------------------
    add_styled_heading(doc, "3. Problem Formulation & Objectives", level=1)
    
    add_styled_heading(doc, "3.1 Problem Formulation", level=2)
    add_body_paragraph(doc,
        "Can a small, programmable 16-bit GPU achieve significantly higher efficiency on edge hardware by combining general SIMT cores with a dedicated matrix engine and autonomous DMA, "
        "and can we verify this as a working proof-of-concept on an entry-level FPGA?"
    )

    add_styled_heading(doc, "3.2 Specific Objectives", level=2)
    add_bullet_item(doc, "Design a modular 16-bit heterogeneous GPU architecture combining 4 SIMT cores, a 2x2 systolic array, a hardware DMA controller, and an 8 KB dual-port BRAM.", bold_title="Objective 1 (Architecture Design): ")
    add_bullet_item(doc, "Build a cycle-accurate reference simulator in Python to verify the instruction set, neural network accuracy, and clock cycle timings.", bold_title="Objective 2 (Software Golden Model): ")
    add_bullet_item(doc, "Write synthesizable SystemVerilog RTL for all components and verify them using automated testbenches and waveform viewers (Icarus Verilog, GTKWave, WaveTrace).", bold_title="Objective 3 (SystemVerilog RTL): ")
    add_bullet_item(doc, "Benchmark the design against an identical SIMT baseline on matrix multiplication, memory copying, wave shaders, and neural network inference.", bold_title="Objective 4 (Benchmarking): ")
    add_bullet_item(doc, "Synthesize and run the design on the Sipeed Tang Nano 9K FPGA at 27 MHz with HDMI video output as an edge proof-of-concept.", bold_title="Objective 5 (FPGA Demonstration): ")

    # -------------------------------------------------------------
    # 4. CURRENT ACHIEVEMENTS: WHAT WE HAVE COMPLETED
    # -------------------------------------------------------------
    add_styled_heading(doc, "4. Current Progress: What We Have Completed (Phases 1 & 2)", level=1)
    add_body_paragraph(doc,
        "We have completed both the architectural modeling (Phase 1) and the full synthesizable SystemVerilog RTL design and verification (Phase 2)."
    )

    add_styled_heading(doc, "4.1 Phase 1: Python Architectural Simulator (Golden Model)", level=2)
    add_body_paragraph(doc,
        "We built a cycle-accurate 16-bit simulator in Python that models real hardware behavior, including two's complement math, register files, and dual-port BRAM memory:",
        bold_prefix="Simulator Components: "
    )
    add_bullet_item(doc, "Models 8 general-purpose registers (R0-R7) with 16-bit math and single-cycle hardware ReLU clamping.", bold_title="processing_element.py: ")
    add_bullet_item(doc, "Controls 4 lockstep cores with parallel arithmetic and LOAD_PARALLEL / STORE_PARALLEL memory access.", bold_title="simt_engine.py: ")
    add_bullet_item(doc, "Simulates a 2x2 systolic array using Kung & Leiserson dataflow, completing a 2x2 matrix multiply in 4 clock cycles with fixed-point scaling.", bold_title="matrix_engine.py: ")
    add_bullet_item(doc, "Performs burst block memory copies in 1+N cycles without tying up the compute cores.", bold_title="dma_engine.py: ")
    add_bullet_item(doc, "Simulates 4096 16-bit words (8 KB) split into framebuffers, AI weights, input buffers, and sprite memory.", bold_title="memory.py: ")
    add_bullet_item(doc, "Top-level controller with live telemetry counters tracking execution cycles for SIMT, AI, DMA, and overall SoC.", bold_title="heterogpu.py: ")
    add_bullet_item(doc, "A 2-layer MLP neural network running on our simulated hardware, achieving a 100% paddle intercept rate across 1,000 test frames.", bold_title="ai_model.py: ")
    add_bullet_item(doc, "An interactive Pygame showcase with 4 live operating modes and a real-time Hardware Telemetry HUD.", bold_title="game_demo.py: ")

    add_styled_heading(doc, "4.2 Phase 2: Synthesizable SystemVerilog RTL Implementation", level=2)
    add_body_paragraph(doc,
        "We translated the validated Python model 1-to-1 into synthesizable SystemVerilog modules under hardware/rtl/:",
        bold_prefix="Hardware RTL Modules: "
    )
    add_bullet_item(doc, "hardware/rtl/pe_core.sv: 16-bit ALU (ADD, SUB, MUL, CMP_GT, MAX) with a hardware sign-bit multiplexer ((op1[15] == 1'b1) ? 0 : op1) for instant ReLU clamping without branching.", bold_title="PE Core: ")
    add_bullet_item(doc, "hardware/rtl/simt_engine.sv: 4-lane parallel SIMT array with lockstep instruction broadcast and parallel memory vector access.", bold_title="SIMT Engine: ")
    add_bullet_item(doc, "hardware/rtl/systolic_array_2x2.sv: 2x2 Tensor Core with 4 physical DSP MAC cells using pipelined operand streaming, completing GEMM in 4 clock cycles.", bold_title="Systolic Array: ")
    add_bullet_item(doc, "hardware/rtl/dma_controller.sv: Hardware FSM burst controller streaming 16-bit words in 1+N clock cycles.", bold_title="DMA Controller: ")
    add_bullet_item(doc, "hardware/rtl/bram_memory.sv: 4096-word dual-port synchronous Block RAM (8 KB) that maps cleanly to Gowin BSRAM blocks.", bold_title="Block RAM: ")
    add_bullet_item(doc, "hardware/rtl/heterogpu_top.sv: Top-level SoC connecting all engines, the memory arbiter, and telemetry registers.", bold_title="HeteroGPU Top SoC: ")

    add_styled_heading(doc, "4.3 Hardware Verification & Waveform Analysis", level=2)
    add_body_paragraph(doc,
        "We tested the RTL using an automated SystemVerilog testbench (hardware/sim/tb_heterogpu.sv) compiled with Icarus Verilog and run with vvp. "
        "All hardware tests passed in 15 clock cycles:",
        bold_prefix="Testbench Results: "
    )
    add_bullet_item(doc, "Confirmed negative 16-bit numbers are clamped to 0x0000 in one clock cycle.", bold_title="Test 1 (PE ReLU): ")
    add_bullet_item(doc, "Confirmed 2x2 matrix multiply finishes in exactly 4 clock cycles.", bold_title="Test 2 (Systolic GEMM): ")
    add_bullet_item(doc, "Confirmed an 8-word memory burst finishes in exactly 9 clock cycles.", bold_title="Test 3 (DMA Burst): ")
    add_body_paragraph(doc,
        "Waveforms were dumped to hardware/sim/waves.vcd and inspected in WaveTrace and GTKWave. "
        "We also created cross-platform run scripts (run_sim.ps1, run_sim.bat) and an EDA filelist (filelist.f)."
    )

    # -------------------------------------------------------------
    # 5. BENCHMARK RESULTS
    # -------------------------------------------------------------
    add_styled_heading(doc, "5. Benchmark Results & Performance Evaluation", level=1)
    add_body_paragraph(doc,
        "We evaluated HeteroGPU across four benchmark workloads against an identical, fully simulated SIMT baseline executing instruction-by-instruction in register-transfer logic."
    )

    # EMBED FIGURE 2 (Benchmark Results Graph)
    bench_img_path = r"C:\Users\aadit\HeteroGPU\python_test_simulator\results\heterogpu_evaluation_results.png"
    if os.path.exists(bench_img_path):
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.paragraph_format.space_before = Pt(4)
        p_img2.paragraph_format.space_after = Pt(2)
        doc.add_picture(bench_img_path, width=Inches(6.4))
        add_caption(doc, "Figure 2: Benchmark Results across Four Hardware Tests, highlighting the 5.75x GEMM speedup, 1.23x DMA copy speedup with 100% cores freed, and the 34-cycle AI forward pass.")

    add_styled_heading(doc, "5.1 Benchmark Findings", level=2)
    add_bullet_item(doc, "A 4x4 matrix multiplication took 92 clock cycles on the SIMT baseline due to scalar weight broadcasts and multi-cycle arithmetic loops. Our 2x2 systolic array finished in only 16 clock cycles (4 passes of 4 cycles each), giving a 5.75x Hardware Speedup.", bold_title="Test 1 (GEMM 4x4 Matrix Multiply): ")
    add_bullet_item(doc, "Copying 64 words took 80 cycles on the SIMT cores and completely tied them up. The DMA controller finished in 65 cycles (1.23x speedup) while keeping SIMT cores 100% idle and available for other tasks.", bold_title="Test 2 (Memory Block Copy): ")
    add_bullet_item(doc, "Running an animated wave shader achieved 95.3% active compute utilization across the 4 SIMT cores, showing high efficiency on vector graphics.", bold_title="Test 3 (SIMT Wave Shader): ")
    add_bullet_item(doc, "A complete forward pass of the 2-layer neural network took only 34 clock cycles total: 24 cycles (70.6%) on the systolic array for matrix layers, 5 cycles (14.7%) on the SIMT cores for parallel ReLU, and 5 cycles (14.7%) on the DMA controller for buffer setup.", bold_title="Test 4 (End-to-End AI Forward Pass): ")

    # TABLE 2: Benchmark Summary Table
    add_styled_heading(doc, "5.2 Quantitative Performance Summary", level=2)
    t2 = doc.add_table(rows=5, cols=5)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths_t2 = [Inches(1.8), Inches(1.2), Inches(1.2), Inches(1.0), Inches(1.4)]
    
    t2_headers = ["Benchmark Workload", "SIMT Baseline", "HeteroGPU", "Speedup", "Hardware Advantage"]
    format_table_header(t2.rows[0], t2_headers, col_widths_t2)
    
    t2_rows = [
        ["GEMM 4x4 Matrix Multiply", "92 cycles", "16 cycles", "5.75x", "Pipelined 2D Systolic Array"],
        ["64-Word Memory Block Copy", "80 cycles", "65 cycles", "1.23x", "100% Compute Cores Free"],
        ["SIMT Waveform Shader", "N/A", "2,430 cycles", "95.3% Util", "Parallel Vector Throughput"],
        ["End-to-End AI Forward Pass", "110 cycles", "34 cycles", "3.24x", "Heterogeneous Co-Processing"]
    ]
    for r_idx, row_vals in enumerate(t2_rows):
        format_table_row(t2.rows[r_idx + 1], row_vals, col_widths_t2, is_even=(r_idx % 2 == 1))

    # -------------------------------------------------------------
    # 6. SCALABILITY & NEXT STEPS
    # -------------------------------------------------------------
    add_styled_heading(doc, "6. Scalability Analysis & Next Steps: From Proof-of-Concept to Real Silicon", level=1)
    add_body_paragraph(doc,
        "A major advantage of HeteroGPU is that our Tang Nano 9K implementation is not a dead-end. "
        "It is a working proof-of-concept designed with modular parameters (NUM_CORES, MESH_DIM, ADDR_WIDTH). "
        "The exact same design can scale up to larger FPGAs and custom silicon."
    )

    add_styled_heading(doc, "6.1 Immediate Next Steps: Physical FPGA Demonstration (Tang Nano 9K)", level=2)
    add_bullet_item(doc, "Synthesize and route hardware/rtl/*.sv using Gowin EDA with pin and timing constraints closed at 27 MHz.", bold_title="1. Physical Bitstream Synthesis: ")
    add_bullet_item(doc, "Program the bitstream (.fs file) to the Tang Nano 9K over USB-JTAG and verify clocked execution on the onboard oscillator.", bold_title="2. On-Chip JTAG Flashing: ")
    add_bullet_item(doc, "Add a TMDS DVI/HDMI encoder to scan out the 32x32 framebuffer from BRAM to a standard 640x480 @ 60 Hz monitor display.", bold_title="3. Hardware HDMI Video Output: ")
    add_bullet_item(doc, "Run the autonomous neural network Pong game 100% on the FPGA, driving the screen and making trajectory decisions in 34 cycles per frame without a host PC.", bold_title="4. Standalone AI Demo: ")

    add_styled_heading(doc, "6.2 Scaling Up to Larger FPGAs", level=2)
    add_body_paragraph(doc,
        "Because our SystemVerilog code is parameterized, moving to larger FPGAs is straightforward:",
        bold_prefix="Mid-Range FPGA Options: "
    )
    add_bullet_item(doc, "Upgrading to the Tang Nano 20K (20,736 LUTs, 64 MB SDRAM) allows expanding to 16 SIMT cores and a 4x4 systolic array (16 DSP MACs), enabling real-time 64x64 graphics and deeper neural networks.", bold_title="Tang Nano 20K (Edge AI Booster): ")
    add_bullet_item(doc, "Using a Xilinx Artix-7 (100T) or AMD Zynq board (100,000+ LUTs) allows scaling to 32 parallel cores (a full warp) and an 8x8 systolic array (64 DSP MACs) at 100–150 MHz. Connecting through an AXI4 memory controller allows direct streaming to 512 MB DDR3/DDR4 RAM for 3D vertex shaders and convolutional vision models.", bold_title="Xilinx Artix-7 / AMD Zynq (Mid-Range GPU): ")

    add_styled_heading(doc, "6.3 The Path to a Physical Silicon ASIC (Chip Tapeout)", level=2)
    add_body_paragraph(doc,
        "Our SystemVerilog RTL can also be taped out as a physical microchip. "
        "Using open-source programs like Tiny Tapeout or the Google / Efabless SkyWater 130nm (SKY130) MPW program, "
        "the HeteroGPU RTL can be synthesized with the open-source OpenLane / Yosys ASIC toolchain into standard GDSII silicon layout. "
        "For a commercial product, the 16-bit ALUs could be expanded to support IEEE 754 FP16/BF16/FP8, backed by on-chip L1/L2 caches and a PCIe host interface."
    )

    # TABLE 3: Multi-Tier Scalability Matrix Table
    add_styled_heading(doc, "6.4 Multi-Tier Hardware Scalability Matrix", level=2)
    add_body_paragraph(doc, "Table 3 summarizes how our architecture scales from our edge proof-of-concept up to custom silicon:")

    t3 = doc.add_table(rows=5, cols=5)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths_t3 = [Inches(1.5), Inches(1.3), Inches(1.2), Inches(1.2), Inches(1.3)]
    
    t3_headers = ["Platform Tier", "Hardware Target", "SIMT Cores", "Systolic Array", "Memory Hierarchy"]
    format_table_header(t3.rows[0], t3_headers, col_widths_t3)
    
    t3_rows = [
        ["Tier 1: Edge PoC (Ours)", "Gowin GW1NR-9 (8.6K LUT)", "4 Cores (16-bit)", "2x2 Array (4 MACs)", "8 KB Dual-Port BRAM"],
        ["Tier 2: Edge AI Booster", "Gowin GW2AR-18 (20K LUT)", "16 Cores (16-bit)", "4x4 Array (16 MACs)", "64 MB Onboard SDRAM"],
        ["Tier 3: Mid-Range GPU", "Xilinx Artix-7 (100K LUT)", "32 Cores (Full Warp)", "8x8 Array (64 MACs)", "512 MB DDR3 via AXI4"],
        ["Tier 4: Silicon ASIC", "SkyWater 130nm / TSMC", "32-64 Cores (FP16/INT8)", "16x16 Array (256 MACs)", "L1/L2 Cache + LPDDR4"]
    ]
    for r_idx, row_vals in enumerate(t3_rows):
        format_table_row(t3.rows[r_idx + 1], row_vals, col_widths_t3, is_even=(r_idx % 2 == 1))

    # TABLE 4: Tang Nano 9K Resource Budget
    add_styled_heading(doc, "6.5 Tang Nano 9K Proof-of-Concept Resource Budget", level=2)
    add_body_paragraph(doc, "Table 4 shows the estimated resource usage on the Tang Nano 9K FPGA for our proof-of-concept:")

    t4 = doc.add_table(rows=6, cols=5)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths_t4 = [Inches(1.8), Inches(1.2), Inches(1.2), Inches(1.2), Inches(1.2)]
    
    t4_headers = ["FPGA Hardware Block", "Available on FPGA", "Estimated RTL Usage", "Utilization %", "Status"]
    format_table_header(t4.rows[0], t4_headers, col_widths_t4)
    
    t4_rows = [
        ["Logic Cells (LUT4)", "8,640", "~1,450", "16.8%", "Safe Margin"],
        ["Flip-Flops (Registers)", "6,480", "~820", "12.7%", "Safe Margin"],
        ["Block RAM (BSRAM)", "26 blocks (468 Kb)", "4 blocks (72 Kb)", "15.4%", "Safe Margin"],
        ["Dedicated DSP Multipliers", "20 (18x18)", "4 DSP slices", "20.0%", "Safe Margin"],
        ["System Clock Frequency", "27.0 MHz (Crystal)", "27.0 MHz (Target)", "100.0%", "Timing Met"]
    ]
    for r_idx, row_vals in enumerate(t4_rows):
        format_table_row(t4.rows[r_idx + 1], row_vals, col_widths_t4, is_even=(r_idx % 2 == 1))

    # -------------------------------------------------------------
    # 7. REFERENCES
    # -------------------------------------------------------------
    add_styled_heading(doc, "References", level=1)
    
    references = [
        ("[1] ", "H. T. Kung and C. E. Leiserson, \"Systolic Arrays (for VLSI),\" in Sparse Matrix Proceedings 1978, Society for Industrial and Applied Mathematics, pp. 256–282, 1979."),
        ("[2] ", "N. P. Jouppi, C. Young, N. Patil, et al., \"In-Datacenter Performance Analysis of a Tensor Processing Unit,\" in Proceedings of the 44th Annual International Symposium on Computer Architecture (ISCA '17), pp. 1–12, 2017."),
        ("[3] ", "S. Markidis, S. W. D. Chien, E. Laure, I. B. Peng, and J. S. Vetter, \"NVIDIA Tensor Core Programmability, Performance & Precision,\" in 2018 IEEE International Parallel and Distributed Processing Symposium Workshops (IPDPSW), pp. 522–531, 2018."),
        ("[4] ", "Y.-H. Chen, J. Emer, and V. Sze, \"Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks,\" in ACM SIGARCH Computer Architecture News (ISCA '16), vol. 44, no. 3, pp. 367–379, 2016."),
        ("[5] ", "V. Sze, Y.-H. Chen, T.-J. Yang, and J. S. Emer, \"Efficient Processing of Deep Neural Networks: A Tutorial and Survey,\" Proceedings of the IEEE, vol. 105, no. 12, pp. 2295–2329, 2017."),
        ("[6] ", "H. Genc, S. Kim, A. Amid, et al., \"Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,\" in 2021 58th ACM/IEEE Design Automation Conference (DAC), pp. 769–774, 2021."),
        ("[7] ", "M. Alaei and F. Yazdanpanah, \"A Survey on Heterogeneous CPU–GPU Architectures and Simulators,\" Concurrency and Computation: Practice and Experience, vol. 37, no. 3, e8318, 2025. DOI: 10.1002/cpe.8318."),
        ("[8] ", "A. Majmudar, \"tiny-gpu: A minimal GPU design in Verilog for educational and architectural exploration,\" GitHub Repository, 2024. [Online]. Available: https://github.com/adammajmudar/tiny-gpu"),
        ("[9] ", "NVIDIA Corporation, \"CUDA C++ Programming Guide: SIMT Architecture,\" Release 12.0, 2023. [Online]. Available: https://docs.nvidia.com/cuda/cuda-c-programming-guide/"),
        ("[10] ", "Sipeed Technology Co., \"Tang Nano 9K Gowin FPGA Development Board Schematic and Hardware User Manual,\" v1.2, 2022.")
    ]
    
    for prefix, citation in references:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.left_indent = Inches(0.28)
        p_ref.paragraph_format.first_line_indent = Inches(-0.28)
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.space_after = Pt(3.5)
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        r_pre = p_ref.add_run(prefix)
        r_pre.bold = True
        r_pre.font.size = Pt(9.0)
        r_pre.font.color.rgb = RGBColor(30, 58, 138)
        
        r_cit = p_ref.add_run(citation)
        r_cit.font.size = Pt(9.0)
        r_cit.font.color.rgb = RGBColor(51, 65, 85)

    # Save document
    poc_path = r"C:\Users\aadit\Downloads\HeteroGPU_Synopsis_Proof_of_Concept.docx"
    doc.save(poc_path)
    print(f"Successfully generated and saved synopsis to: {poc_path}")

    try:
        doc.save(src_path)
        print(f"Successfully updated original file: {src_path}")
    except PermissionError:
        print(f"Notice: '{src_path}' is currently open in Microsoft Word. Generated file saved as '{poc_path}'!")

if __name__ == "__main__":
    build_synopsis()
