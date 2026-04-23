module abs_diff_i49152_o24576(a,b,r);
input [24575:0] a,b;
output [24575:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
