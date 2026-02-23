module madd_i114_o76 (a, b, c, r);
input [37:0] a,b,c;
output [75:0] r;

assign r = (a * b) + c;

endmodule
