module madd_i369_o246 (a, b, c, r);
input [122:0] a,b,c;
output [245:0] r;

assign r = (a * b) + c;

endmodule
