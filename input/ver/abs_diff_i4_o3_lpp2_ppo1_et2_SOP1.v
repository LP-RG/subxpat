module abs_diff_i4_o3_lpp2_ppo1_et2_SOP1 (in0, in1, in2, in3, out0, out1);
input in0, in1, in2, in3;
output out0, out1;
//intact gates wires 
wire w_g15, w_g16, w_g17, w_g18, w_g19;
//annotated subgraph inputs
wire w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g12, w_g13, w_g14;
//json model
wire p_o0_t0, p_o1_t0, p_o2_t0;
//subgraph inputs assigns
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = ~w_in1 & w_in3;
assign w_g12 = p_o0_t0;
assign p_o1_t0 = w_in2 & ~w_in3;
assign w_g13 = p_o1_t0;
assign p_o2_t0 = w_in0 & ~w_in1;
assign w_g14 = p_o2_t0;
// intact gates assigns
assign w_g15 = ~w_g12;
assign w_g16 = ~w_g13;
assign w_g17 = ~w_g14;
assign w_g18 = w_g16 & w_g15;
assign w_g19 = ~w_g18;
// output assigns
assign out0 = w_g17;
assign out1 = w_g19;
endmodule