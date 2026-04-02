module madd_i219_o146 (a, b, c, r);
input [72:0] a,b,c;
output [145:0] r;

assign r = (a * b) + c;

endmodule
