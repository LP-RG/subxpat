module mul_i4_o4_lpp1_ppo1_et2_SOP1 (in0, in1, in2, in3, out0, out1, out2, out3);
//input/output declarations
input in0, in1, in2, in3;
output out0, out1, out2, out3;
//intact gates wires 
wire w_g12, w_g14, w_g16, w_g17, w_g18, w_g19, w_g20;
//annotated subgraph inputs
wire w_in3, w_in2, w_in0, w_g0, w_g1;
//annotated subgraph outputs
wire w_g8, w_g9, w_g10, w_g15;
//json input wires
wire j_in0, j_in1, j_in2, j_in3, j_in4;
//json model
wire p_o0_t0, p_o1_t0, p_o2_t0, p_o3_t0;
//subgraph inputs assigns
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in0 = in0;
assign w_g0 = in3 & in1;
assign w_g1 = in2 & in1;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in0;
assign j_in1 = w_in2;
assign j_in2 = w_in3;
assign j_in3 = w_g0;
assign j_in4 = w_g1;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = ~j_in0;
assign w_g8 = p_o0_t0;
assign p_o1_t0 = ~j_in2;
assign w_g9 = p_o1_t0;
assign p_o2_t0 = j_in0;
assign w_g10 = p_o2_t0;
assign p_o3_t0 = j_in3;
assign w_g15 = p_o3_t0;
// intact gates assigns
assign w_g0 = w_in3 & in1;
assign w_g1 = w_in2 & in1;
assign w_g12 = ~w_g9;
assign w_g14 = out0 & w_g8;
assign w_g16 = ~w_g14;
assign w_g17 = w_g12 & w_g16;
assign w_g18 = ~w_g16;
assign w_g19 = ~w_g17;
assign w_g20 = ~w_g19;
// output assigns
assign out0 = w_g10;
assign out1 = w_g20;
assign out2 = w_g15;
assign out3 = w_g18;
endmodule