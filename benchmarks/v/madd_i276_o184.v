module madd_i276_o184 (a, b, c, r);
input [91:0] a,b,c;
output [183:0] r;

assign r = (a * b) + c;

endmodule
