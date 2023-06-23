module adder_i4_o3_lpp2_ppo1_et4_SOP1 (in0, in1, in2, in3, out0, out1, out2);
input in0, in1, in2, in3;
output out0, out1, out2;
//intact gates wires 
wire w_g15, w_g16, w_g17, w_g18, w_g19, w_g20, w_g21, w_g22, w_g23, w_g24;
//annotated subgraph inputs
wire w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g4, w_g6, w_g9, w_g10, w_g13, w_g14;
//json model
wire p_o0_t0, p_o1_t0, p_o2_t0, p_o3_t0, p_o4_t0, p_o5_t0;
//subgraph inputs assigns
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = w_in1 & w_in2;
assign w_g4 = p_o0_t0;
assign p_o1_t0 = w_in0;
assign w_g6 = p_o1_t0;
assign p_o2_t0 = ~w_in0 & ~w_in1;
assign w_g9 = p_o2_t0;
assign p_o3_t0 = w_in3;
assign w_g10 = p_o3_t0;
assign p_o4_t0 = w_in1;
assign w_g13 = p_o4_t0;
assign p_o5_t0 = ~w_in0 & w_in1 & w_in3;
assign w_g14 = p_o5_t0;
// intact gates assigns
assign w_g15 = w_g13 & w_g10;
assign w_g16 = ~w_g14;
assign w_g17 = w_g4 & w_g14;
assign w_g18 = w_g16 & w_g9;
assign w_g19 = ~w_g17;
assign w_g20 = ~w_g17;
assign w_g21 = ~w_g18;
assign w_g22 = w_g19 & w_g6;
assign w_g23 = w_g21 & w_g20;
assign w_g24 = ~w_g22;
// output assigns
assign out0 = w_g15;
assign out1 = w_g23;
assign out2 = w_g24;
endmodule