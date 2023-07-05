module abs_diff_i4_o3_lpp1_ppo4_et4_SOP1 (in0, in1, in2, in3, out0, out1);
//input/output declarations
input in0, in1, in2, in3;
output out0, out1;
//intact gates wires 
wire w_g16, w_g17, w_g18, w_g19, w_g20, w_g21;
//annotated subgraph inputs
wire w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g9, w_g13, w_g14, w_g15;
// no json wires!
//json model
wire p_o0_t0, p_o0_t1, p_o0_t2, p_o0_t3, p_o1_t0, p_o1_t1, p_o1_t2, p_o1_t3, p_o2_t0, p_o2_t1, p_o2_t2, p_o2_t3, p_o3_t0, p_o3_t1, p_o3_t2, p_o3_t3;
//subgraph inputs assigns
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//mapping subgraph inputs to json inputs
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = w_in3;
assign p_o0_t1 = ~w_in2;
assign p_o0_t2 = ~w_in0;
assign p_o0_t3 = ~w_in0;
assign w_g9 = p_o0_t0 | p_o0_t1 | p_o0_t2 | p_o0_t3;
assign p_o1_t0 = w_in3;
assign p_o1_t1 = w_in3;
assign p_o1_t2 = ~w_in2;
assign p_o1_t3 = w_in0;
assign w_g13 = p_o1_t0 | p_o1_t1 | p_o1_t2 | p_o1_t3;
assign p_o2_t0 = w_in3;
assign p_o2_t1 = w_in0;
assign p_o2_t2 = ~w_in2;
assign p_o2_t3 = w_in3;
assign w_g14 = p_o2_t0 | p_o2_t1 | p_o2_t2 | p_o2_t3;
assign p_o3_t0 = ~w_in3;
assign p_o3_t1 = ~w_in0;
assign p_o3_t2 = ~w_in2;
assign p_o3_t3 = 1;
assign w_g15 = p_o3_t0 | p_o3_t1 | p_o3_t2 | p_o3_t3;
// intact gates assigns
assign w_g16 = w_g13 & w_g9;
assign w_g17 = ~w_g14;
assign w_g18 = ~w_g15;
assign w_g19 = ~w_g16;
assign w_g20 = w_g18 & w_g19;
assign w_g21 = ~w_g20;
// output assigns
assign out0 = w_g17;
assign out1 = w_g21;
endmodule