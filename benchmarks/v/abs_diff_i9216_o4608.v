module abs_diff_i9216_o4608(a,b,r);
input [4607:0] a,b;
output [4607:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
