module madd_i5760_o3840 (a, b, c, r);
input [1919:0] a,b,c;
output [3839:0] r;

assign r = (a * b) + c;

endmodule
