module madd_i342_o228 (a, b, c, r);
input [113:0] a,b,c;
output [227:0] r;

assign r = (a * b) + c;

endmodule
