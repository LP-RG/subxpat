module madd_i54_o36 (a, b, c, r);
input [17:0] a,b,c;
output [35:0] r;

assign r = (a * b) + c;

endmodule
