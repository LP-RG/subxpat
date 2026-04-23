module madd_i1536_o1024 (a, b, c, r);
input [511:0] a,b,c;
output [1023:0] r;

assign r = (a * b) + c;

endmodule
