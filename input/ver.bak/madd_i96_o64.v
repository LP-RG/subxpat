module madd_i96_o64 (a, b, c, r);
input [31:0] a,b,c;
output [63:0] r;

assign r = (a * b) + c;

endmodule
