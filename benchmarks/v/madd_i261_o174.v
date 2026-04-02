module madd_i261_o174 (a, b, c, r);
input [86:0] a,b,c;
output [173:0] r;

assign r = (a * b) + c;

endmodule
