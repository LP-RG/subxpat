module madd_i48_o32 (a, b, c, r);
input [15:0] a,b,c;
output [31:0] r;

assign r = (a * b) + c;

endmodule
