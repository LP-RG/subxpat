module abs_diff_i528_o264(a,b,r);
input [263:0] a,b;
output [263:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
