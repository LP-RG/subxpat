module buttfly_i32_o34 (a,b,r1,r2);
input [15:0] a,b;
output [16:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
