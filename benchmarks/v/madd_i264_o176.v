module madd_i264_o176 (a, b, c, r);
input [87:0] a,b,c;
output [175:0] r;

assign r = (a * b) + c;

endmodule
