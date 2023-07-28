module adder_i8_o5_lpp1_ppo2_et6_SOP1_pap50_iter1 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3, out4);
//input/output declarations
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3, out4;
//intact gates wires 
wire w_g34, w_g35, w_g36, w_g37, w_g38, w_g39, w_g40, w_g41, w_g42, w_g43, w_g44, w_g45, w_g46, w_g47, w_g48, w_g49, w_g50, w_g51, w_g52, w_g53, w_g54, w_g55, w_g56, w_g57, w_g58, w_g59, w_g60, w_g61, w_g62, w_g63, w_g64, w_g65;
//annotated subgraph inputs
wire w_in7, w_in6, w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g12, w_g14, w_g16, w_g18, w_g23, w_g29, w_g30, w_g31, w_g32, w_g33;
//json input wires
wire j_in0, j_in1, j_in2, j_in3, j_in4, j_in5, j_in6, j_in7;
//json model
wire p_o0_t0, p_o0_t1, p_o1_t0, p_o1_t1, p_o2_t0, p_o2_t1, p_o3_t0, p_o3_t1, p_o4_t0, p_o4_t1, p_o5_t0, p_o5_t1, p_o6_t0, p_o6_t1, p_o7_t0, p_o7_t1, p_o8_t0, p_o8_t1, p_o9_t0, p_o9_t1;
//subgraph inputs assigns
assign w_in7 = in7;
assign w_in6 = in6;
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in0;
assign j_in1 = w_in1;
assign j_in2 = w_in2;
assign j_in3 = w_in3;
assign j_in4 = w_in4;
assign j_in5 = w_in5;
assign j_in6 = w_in6;
assign j_in7 = w_in7;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = ~j_in7;
assign p_o0_t1 = ~j_in5;
assign w_g12 = p_o0_t0 | p_o0_t1;
assign p_o1_t0 = ~j_in7;
assign p_o1_t1 = j_in5;
assign w_g14 = p_o1_t0 | p_o1_t1;
assign p_o2_t0 = j_in7;
assign p_o2_t1 = j_in1;
assign w_g16 = p_o2_t0 | p_o2_t1;
assign p_o3_t0 = ~j_in2;
assign p_o3_t1 = ~j_in1;
assign w_g18 = p_o3_t0 | p_o3_t1;
assign p_o4_t0 = ~j_in6;
assign p_o4_t1 = j_in5;
assign w_g23 = p_o4_t0 | p_o4_t1;
assign p_o5_t0 = ~j_in3;
assign p_o5_t1 = ~j_in3;
assign w_g29 = p_o5_t0 | p_o5_t1;
assign p_o6_t0 = ~j_in6;
assign p_o6_t1 = ~j_in6;
assign w_g30 = p_o6_t0 | p_o6_t1;
assign p_o7_t0 = j_in7;
assign p_o7_t1 = ~j_in4;
assign w_g31 = p_o7_t0 | p_o7_t1;
assign p_o8_t0 = j_in4;
assign p_o8_t1 = ~j_in2;
assign w_g32 = p_o8_t0 | p_o8_t1;
assign p_o9_t0 = j_in3;
assign p_o9_t1 = j_in3;
assign w_g33 = p_o9_t0 | p_o9_t1;
// intact gates assigns
assign w_g34 = ~w_g30;
assign w_g35 = w_g31 & w_g18;
assign w_g36 = ~w_g31;
assign w_g37 = ~w_g32;
assign w_g38 = ~w_g35;
assign w_g39 = w_g36 & w_g23;
assign w_g40 = ~w_g39;
assign w_g41 = w_g38 & w_g40;
assign w_g42 = w_g40 & w_g16;
assign w_g43 = ~w_g41;
assign w_g44 = ~w_g42;
assign w_g45 = ~w_g43;
assign w_g46 = w_g34 & w_g44;
assign w_g47 = ~w_g44;
assign w_g48 = ~w_g46;
assign w_g49 = w_g47 & w_g30;
assign w_g50 = w_g48 & w_g14;
assign w_g51 = ~w_g49;
assign w_g52 = ~w_g50;
assign w_g53 = w_g51 & w_g48;
assign w_g54 = w_g33 & w_g52;
assign w_g55 = ~w_g52;
assign w_g56 = ~w_g53;
assign w_g57 = ~w_g54;
assign w_g58 = w_g55 & w_g29;
assign w_g59 = ~w_g56;
assign w_g60 = w_g57 & w_g12;
assign w_g61 = ~w_g58;
assign w_g62 = ~w_g60;
assign w_g63 = w_g61 & w_g57;
assign w_g64 = ~w_g63;
assign w_g65 = ~w_g64;
// output assigns
assign out0 = w_g37;
assign out1 = w_g45;
assign out2 = w_g59;
assign out3 = w_g65;
assign out4 = w_g62;
endmodule